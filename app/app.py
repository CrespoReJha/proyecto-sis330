import cv2
from ultralytics import YOLO
from collections import deque
import numpy as np
import time
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from enum import Enum
from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import sqlite3
import base64
import io
from PIL import Image

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Parámetros ajustables
MODEL_PATH = "/home/jhamilcr/Documents/proyecto-sis330/detection-model/train-files/best.pt"
MIN_CONF = 0.8
STABILITY_FRAMES = 20
EXCLUDED_CLASS = "hand"
IOU_THRESHOLD = 0.35
CENTER_DISTANCE_THRESHOLD = 80
SIZE_RATIO_THRESHOLD = 0.5
OVERLAP_THRESHOLD = 0.5
PRODUCT_TIMEOUT = 3.0
MIN_DETECTION_FRAMES = 8
OCCLUSION_TOLERANCE = 0.55
REMOVAL_CONFIRMATION_FRAMES = 30
PROCESS_EVERY_N_FRAMES = 3
FRAME_SKIP_ON_STABLE = 5
OCCLUSION_TIMEOUT = 1000.0
LAYER_DEPTH_THRESHOLD = 0.7
RECOVERY_FRAMES = 5
MAX_LAYERS = 5

class ProductState(Enum):
    DETECTING = "detecting"
    VISIBLE = "visible"
    OCCLUDED = "occluded"
    RECOVERING = "recovering"
    REMOVED = "removed"

@dataclass
class Product:
    id: str
    class_name: str
    bbox: Tuple[int, int, int, int]
    confidence: float
    first_seen: float
    last_seen: float
    last_visible: float
    detection_count: int
    confirmed: bool
    removal_count: int
    state: ProductState
    layer: int
    occlusion_start: Optional[float]
    recovery_count: int
    occluded_by: List[str]
    historical_positions: deque

class LayeredShoppingCart:
    def __init__(self):
        self.products: Dict[str, Product] = {}
        self.next_id = 1
        self.detection_history = deque(maxlen=STABILITY_FRAMES)
        self.last_stable_count = 0
        self.stability_counter = 0
        self.last_detection_time = 0
        self.spatial_grid = {}
        
    def should_process_frame(self, frame_count: int, current_time: float) -> bool:
        if frame_count < PROCESS_EVERY_N_FRAMES * 2:
            return True
        if frame_count % PROCESS_EVERY_N_FRAMES != 0:
            return False
        current_count = len([p for p in self.products.values() 
                           if p.state in [ProductState.VISIBLE, ProductState.OCCLUDED]])
        if current_count == self.last_stable_count:
            self.stability_counter += 1
        else:
            self.stability_counter = 0
        self.last_stable_count = current_count
        if self.stability_counter > 10:
            return frame_count % (PROCESS_EVERY_N_FRAMES + FRAME_SKIP_ON_STABLE) == 0
        return True
    
    def get_detection_interval(self) -> int:
        if self.stability_counter > 10:
            return PROCESS_EVERY_N_FRAMES + FRAME_SKIP_ON_STABLE
        return PROCESS_EVERY_N_FRAMES
    
    def generate_product_id(self, class_name: str) -> str:
        product_id = f"{class_name}_{self.next_id}"
        self.next_id += 1
        return product_id
    
    def compute_iou(self, boxA: Tuple, boxB: Tuple) -> float:
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interW = max(0, xB - xA)
        interH = max(0, yB - yA)
        interArea = interW * interH
        if interArea == 0:
            return 0.0
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        unionArea = boxAArea + boxBArea - interArea
        return interArea / unionArea if unionArea > 0 else 0.0
    
    def compute_center_distance(self, boxA: Tuple, boxB: Tuple) -> float:
        centerA = ((boxA[0] + boxA[2]) / 2, (boxA[1] + boxA[3]) / 2)
        centerB = ((boxB[0] + boxB[2]) / 2, (boxB[1] + boxB[3]) / 2)
        return np.sqrt((centerA[0] - centerB[0])**2 + (centerA[1] - centerB[1])**2)
    
    def estimate_depth_layer(self, product_id: str, detections: List[Tuple]) -> int:
        occlusion_graph = {pid: set() for pid in self.products}
        for pid, product in self.products.items():
            if product.state == ProductState.REMOVED:
                continue
            for occluder_id in product.occluded_by:
                for other_pid, other_product in self.products.items():
                    if other_product.state == ProductState.REMOVED:
                        continue
                    if occluder_id.startswith(other_product.class_name):
                        occlusion_graph[pid].add(other_pid)
                        break
        return self.assign_layers_from_occlusion_graph(occlusion_graph, product_id)
    
    def assign_layers_from_occlusion_graph(self, occlusion_graph: Dict[str, set], product_id: str) -> int:
        if product_id not in occlusion_graph:
            return 0
        visited = set()
        memo = {}
        def get_max_depth(pid: str) -> int:
            if pid in memo:
                return memo[pid]
            if pid in visited:
                return 0
            visited.add(pid)
            max_depth = 0
            for occluder in occlusion_graph[pid]:
                max_depth = max(max_depth, get_max_depth(occluder) + 1)
            visited.remove(pid)
            memo[pid] = max_depth
            return max_depth
        layer = get_max_depth(product_id)
        return min(layer, MAX_LAYERS - 1)
    
    def compute_overlap_ratio(self, boxA: Tuple, boxB: Tuple) -> Tuple[float, float]:
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        interW = max(0, xB - xA)
        interH = max(0, yB - yA)
        interArea = interW * interH
        if interArea == 0:
            return 0.0, 0.0
        areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        overlapA = interArea / areaA if areaA > 0 else 0
        overlapB = interArea / areaB if areaB > 0 else 0
        return overlapA, overlapB
    
    def predict_occluded_position(self, product: Product) -> Tuple[int, int, int, int]:
        if len(product.historical_positions) < 2:
            return product.bbox
        recent_positions = list(product.historical_positions)[-3:]
        if len(recent_positions) < 2:
            return product.bbox
        dx_total = dy_total = 0
        for i in range(1, len(recent_positions)):
            prev_center = ((recent_positions[i-1][0] + recent_positions[i-1][2]) / 2,
                          (recent_positions[i-1][1] + recent_positions[i-1][3]) / 2)
            curr_center = ((recent_positions[i][0] + recent_positions[i][2]) / 2,
                          (recent_positions[i][1] + recent_positions[i][3]) / 2)
            dx_total += curr_center[0] - prev_center[0]
            dy_total += curr_center[1] - prev_center[1]
        velocity_frames = len(recent_positions) - 1
        avg_dx = dx_total / velocity_frames if velocity_frames > 0 else 0
        avg_dy = dy_total / velocity_frames if velocity_frames > 0 else 0
        last_bbox = recent_positions[-1]
        width = last_bbox[2] - last_bbox[0]
        height = last_bbox[3] - last_bbox[1]
        predicted_center_x = (last_bbox[0] + last_bbox[2]) / 2 + avg_dx
        predicted_center_y = (last_bbox[1] + last_bbox[3]) / 2 + avg_dy
        return (
            int(predicted_center_x - width/2),
            int(predicted_center_y - height/2),
            int(predicted_center_x + width/2),
            int(predicted_center_y + height/2)
        )
    
    def analyze_occlusions(self, detections: List[Tuple], current_time: float):
        temp_occluded_by = {pid: product.occluded_by.copy() for pid, product in self.products.items()}
        available_detections = detections.copy()
        used_detections = set()
        for product_id, product in self.products.items():
            if product.state in [ProductState.VISIBLE, ProductState.RECOVERING]:
                best_score = 0
                best_idx = -1
                for i, detection in enumerate(available_detections):
                    if i in used_detections:
                        continue
                    if self.is_same_product(product, detection):
                        class_name, x1, y1, x2, y2, conf = detection
                        det_bbox = (x1, y1, x2, y2)
                        iou = self.compute_iou(product.bbox, det_bbox)
                        center_dist = self.compute_center_distance(product.bbox, det_bbox)
                        score = iou * 0.6 + (1 - min(center_dist / CENTER_DISTANCE_THRESHOLD, 1.0)) * 0.4
                        if score > best_score:
                            best_score = score
                            best_idx = i
                if best_idx != -1:
                    used_detections.add(best_idx)
        sorted_products = sorted(self.products.items(), key=lambda x: x[1].first_seen)
        for product_id, product in sorted_products:
            if product.state == ProductState.REMOVED:
                temp_occluded_by[product_id] = []
                continue
            check_bbox = self.predict_occluded_position(product) if product.state == ProductState.OCCLUDED else product.bbox
            is_occluded = False
            occluding_objects = []
            for other_pid, other_p in sorted_products:
                if other_pid == product_id or other_p.state == ProductState.REMOVED:
                    continue
                if other_p.layer >= product.layer and other_p.first_seen <= product.first_seen:
                    continue
                other_bbox = self.predict_occluded_position(other_p) if other_p.state == ProductState.OCCLUDED else other_p.bbox
                overlap_ratio = self.compute_overlap_ratio(check_bbox, other_bbox)[0]
                if overlap_ratio > OCCLUSION_TOLERANCE:
                    occluding_objects.append(other_pid)
                    is_occluded = True
            for i, detection in enumerate(available_detections):
                if i in used_detections:
                    continue
                class_name, x1, y1, x2, y2, conf = detection
                det_bbox = (x1, y1, x2, y2)
                overlap_ratio = self.compute_overlap_ratio(check_bbox, det_bbox)[0]
                if overlap_ratio > OCCLUSION_TOLERANCE:
                    matched_product_id = None
                    for other_pid, other_p in self.products.items():
                        if other_pid == product_id or other_p.state == ProductState.REMOVED:
                            continue
                        if self.is_same_product(other_p, detection) and other_p.layer < product.layer:
                            matched_product_id = other_pid
                            if matched_product_id not in occluding_objects:
                                occluding_objects.append(matched_product_id)
                            break
                    is_occluded = True
                    if not matched_product_id:
                        occluder_id = f"{class_name}_{x1}_{y1}"
                        if occluder_id not in occluding_objects:
                            occluding_objects.append(occluder_id)
            temp_occluded_by[product_id] = occluding_objects
            if is_occluded and product.state == ProductState.VISIBLE:
                product.state = ProductState.OCCLUDED
                product.occlusion_start = current_time
                product.removal_count = 0
                print(f"OCLUIDO: {product.id} por {len(occluding_objects)} objeto(s): {occluding_objects}")
            elif product.state == ProductState.OCCLUDED:
                is_detected = any(self.is_same_product(product, detection) 
                                for i, detection in enumerate(available_detections) 
                                if i not in used_detections)
                if is_detected and not is_occluded:
                    product.state = ProductState.RECOVERING
                    product.recovery_count = 0
                    product.occlusion_start = None
                    product.removal_count = 0
                    print(f"RECUPERANDO: {product.id}")
                elif is_occluded:
                    product.removal_count = 0
                elif not is_occluded and not is_detected:
                    product.removal_count += max(1, PROCESS_EVERY_N_FRAMES // 3)
        for product_id, product in self.products.items():
            product.occluded_by = [oid for oid in temp_occluded_by[product_id] 
                                if oid in self.products and self.products[oid].state != ProductState.REMOVED]
    
    def is_same_product(self, product: Product, detection: Tuple) -> bool:
        class_name, x1, y1, x2, y2, conf = detection
        if product.class_name != class_name:
            return False
        det_bbox = (x1, y1, x2, y2)
        check_bbox = self.predict_occluded_position(product) if product.state == ProductState.OCCLUDED else product.bbox
        iou = self.compute_iou(check_bbox, det_bbox)
        center_dist = self.compute_center_distance(check_bbox, det_bbox)
        overlap_a, overlap_b = self.compute_overlap_ratio(check_bbox, det_bbox)
        size_ratio = min(
            (check_bbox[2] - check_bbox[0]) / (det_bbox[2] - det_bbox[0]),
            (det_bbox[2] - det_bbox[0]) / (check_bbox[2] - check_bbox[0])
        )
        estimated_layer = self.estimate_depth_layer(product.id, [(class_name, x1, y1, x2, y2, conf)])
        layer_diff = abs(product.layer - estimated_layer)
        layer_penalty = 1.0 - (0.1 * layer_diff) if product.state != ProductState.DETECTING else 1.0
        movement_consistency = 1.0
        if len(product.historical_positions) >= 2 and product.state != ProductState.DETECTING:
            last_pos = product.historical_positions[-1]
            second_last_pos = product.historical_positions[-2]
            last_dx = (last_pos[0] + last_pos[2]) / 2 - (second_last_pos[0] + second_last_pos[2]) / 2
            last_dy = (last_pos[1] + last_pos[3]) / 2 - (second_last_pos[1] + second_last_pos[3]) / 2
            curr_dx = (det_bbox[0] + det_bbox[2]) / 2 - (last_pos[0] + last_pos[2]) / 2
            curr_dy = (det_bbox[1] + det_bbox[3]) / 2 - (last_pos[1] + last_pos[3]) / 2
            movement_diff = np.sqrt((last_dx - curr_dx)**2 + (last_dy - curr_dy)**2)
            movement_consistency = max(0, 1.0 - movement_diff / CENTER_DISTANCE_THRESHOLD)
        score = (
            iou * 0.5 +
            (1 - min(center_dist / CENTER_DISTANCE_THRESHOLD, 1.0)) * 0.3 +
            max(overlap_a, overlap_b) * 0.1 +
            size_ratio * 0.05 +
            movement_consistency * 0.05
        ) * layer_penalty
        return score >= 0.6
    
    def find_matching_products(self, detections: List[Tuple]) -> Tuple[Dict[str, Optional[Tuple]], set]:
        matches = {}
        used_detections = set()
        sorted_products = sorted(
            self.products.items(),
            key=lambda x: (
                0 if x[1].state == ProductState.VISIBLE else
                1 if x[1].state == ProductState.RECOVERING else
                2 if x[1].state == ProductState.OCCLUDED else 3,
                x[1].layer
            )
        )
        for product_id, product in sorted_products:
            if product.state == ProductState.REMOVED:
                matches[product_id] = None
                continue
            best_match = None
            best_score = 0
            best_idx = -1
            for i, detection in enumerate(detections):
                if i in used_detections:
                    continue
                if self.is_same_product(product, detection):
                    class_name, x1, y1, x2, y2, conf = detection
                    det_bbox = (x1, y1, x2, y2)
                    check_bbox = self.predict_occluded_position(product) if product.state == ProductState.OCCLUDED else product.bbox
                    iou = self.compute_iou(check_bbox, det_bbox)
                    center_dist = self.compute_center_distance(check_bbox, det_bbox)
                    if product.state == ProductState.OCCLUDED:
                        score = iou * 0.7 + (1 - min(center_dist / (CENTER_DISTANCE_THRESHOLD * 1.5), 1.0)) * 0.3
                    else:
                        score = iou * 0.6 + (1 - min(center_dist / CENTER_DISTANCE_THRESHOLD, 1.0)) * 0.4
                    if score > best_score:
                        best_score = score
                        best_match = detection
                        best_idx = i
            if best_match is not None:
                matches[product_id] = best_match
                used_detections.add(best_idx)
            else:
                matches[product_id] = None
        return matches, used_detections
    
    def update_cart(self, detections: List[Tuple], current_time: float) -> Dict:
        changes = {
            'added': [],
            'updated': [],
            'removed': [],
            'maintained': [],
            'occluded': [],
            'recovered': []
        }
        self.analyze_occlusions(detections, current_time)
        for product_id in list(self.products.keys()):
            product = self.products[product_id]
            if product.confirmed and product.state != ProductState.REMOVED:
                product.layer = self.estimate_depth_layer(product_id, detections)
        matches, used_detections = self.find_matching_products(detections)
        products_to_remove = []
        for product_id, detection in matches.items():
            product = self.products[product_id]
            if detection is not None:
                class_name, x1, y1, x2, y2, conf = detection
                new_bbox = (x1, y1, x2, y2)
                if len(product.historical_positions) == 0 or product.historical_positions[-1] != new_bbox:
                    product.historical_positions.append(new_bbox)
                product.bbox = new_bbox
                product.confidence = conf
                product.last_seen = current_time
                product.last_visible = current_time
                product.detection_count += 1
                product.removal_count = 0
                if product.state == ProductState.DETECTING:
                    if product.detection_count >= MIN_DETECTION_FRAMES:
                        product.confirmed = True
                        product.state = ProductState.VISIBLE
                        changes['added'].append(product_id)
                        print(f"AGREGADO: {product.class_name} (ID: {product_id}, Capa: {product.layer})")
                        for other_pid, other_p in self.products.items():
                            if other_pid != product_id and other_p.state != ProductState.REMOVED:
                                updated_occluders = []
                                for occluder_id in other_p.occluded_by:
                                    if occluder_id.startswith(product.class_name) and not occluder_id.startswith(product.id):
                                        updated_occluders.append(product_id)
                                    else:
                                        updated_occluders.append(occluder_id)
                                other_p.occluded_by = updated_occluders
                    else:
                        changes['updated'].append(product_id)
                elif product.state == ProductState.RECOVERING:
                    product.recovery_count += 1
                    if product.state == ProductState.VISIBLE:
                        changes['recovered'].append(product_id)
                        print(f"RECUPERADO: {product.class_name} ({product_id})")
                    else:
                        changes['updated'].append(product_id)
                elif product.state == ProductState.VISIBLE:
                    changes['maintained'].append(product_id)
                    print(f"VISIBLE: {product.class_name} (ID: {product_id}, Capa: {product.layer})")
                elif product.state == ProductState.OCCLUDED:
                    product.state = ProductState.RECOVERING
                    product.recovery_count = 1
                    product.removalvoice_count = 0
                    changes['updated'].append(product_id)
            else:
                if product.state == ProductState.OCCLUDED:
                    if product.occluded_by or (current_time - product.occlusion_start <= 3.0):
                        changes['maintained'].append(product_id)
                    else:
                        adjusted_removal_threshold = max(REMOVAL_CONFIRMATION_FRAMES // PROCESS_EVERY_N_FRAMES, 2)
                        if current_time - product.occlusion_start > OCCLUSION_TIMEOUT or product.removal_count >= adjusted_removal_threshold:
                            products_to_remove.append(product_id)
                        else:
                            changes['maintained'].append(product_id)
                elif product.state in [ProductState.VISIBLE, ProductState.RECOVERING]:
                    removal_increment = max(1, PROCESS_EVERY_N_FRAMES // 3)
                    product.removal_count += removal_increment
                    adjusted_removal_threshold = max(REMOVAL_CONFIRMATION_FRAMES // PROCESS_EVERY_N_FRAMES, 2)
                    if product.confirmed and product.removal_count >= adjusted_removal_threshold:
                        products_to_remove.append(product_id)
                    elif not product.confirmed and (current_time - product.last_seen) > PRODUCT_TIMEOUT / 2:
                        products_to_remove.append(product_id)
                elif product.state == ProductState.DETECTING:
                    if (current_time - product.last_seen) > PRODUCT_TIMEOUT / 2:
                        products_to_remove.append(product_id)
        for product_id in products_to_remove:
            removed_product = self.products.pop(product_id)
            removed_product.state = ProductState.REMOVED
            if removed_product.confirmed:
                changes['removed'].append(product_id)
                print(f"REMOVIDO: {product_id}")
            for other_pid, other_p in self.products.items():
                if product_id in other_p.occluded_by:
                    other_p.occluded_by.remove(product_id)
        for i, detection in enumerate(detections):
            if i not in used_detections:
                class_name, x1, y1, x2, y2, conf = detection
                product_id = self.generate_product_id(class_name)
                new_bbox = (x1, y1, x2, y2)
                historical_positions = deque(maxlen=10)
                historical_positions.append(new_bbox)
                new_product = Product(
                    id=product_id,
                    class_name=class_name,
                    bbox=new_bbox,
                    confidence=conf,
                    first_seen=current_time,
                    last_seen=current_time,
                    last_visible=current_time,
                    detection_count=1,
                    confirmed=False,
                    removal_count=0,
                    state=ProductState.DETECTING,
                    layer=self.estimate_depth_layer(product_id, detections),
                    occlusion_start=None,
                    recovery_count=0,
                    occluded_by=[],
                    historical_positions=historical_positions
                )
                self.products[product_id] = new_product
                changes['updated'].append(product_id)
        return changes
    
    def get_cart_summary(self) -> Dict:
        confirmed_products = {pid: p for pid, p in self.products.items() 
                            if p.confirmed and p.state != ProductState.REMOVED}
        visible_products = {pid: p for pid, p in confirmed_products.items() 
                          if p.state == ProductState.VISIBLE}
        occluded_products = {pid: p for pid, p in confirmed_products.items() 
                           if p.state == ProductState.OCCLUDED}
        recovering_products = {pid: p for pid, p in confirmed_products.items() 
                             if p.state == ProductState.RECOVERING}
        pending_products = {pid: p for pid, p in self.products.items() 
                          if p.state == ProductState.DETECTING}
        class_counts = {}
        for product in confirmed_products.values():
            class_counts[product.class_name] = class_counts.get(product.class_name, 0) + 1
        return {
            'confirmed_count': len(confirmed_products),
            'visible_count': len(visible_products),
            'occluded_count': len(occluded_products),
            'recovering_count': len(recovering_products),
            'pending_count': len(pending_products),
            'total_count': len(self.products),
            'class_counts': class_counts,
            'confirmed_products': confirmed_products,
            'visible_products': visible_products,
            'occluded_products': occluded_products,
            'recovering_products': recovering_products,
            'pending_products': pending_products
        }

def get_detections(frame, model, min_conf):
    results = model.predict(source=frame, save=False, verbose=False)[0]
    detections = []
    for box in results.boxes:
        conf = float(box.conf)
        if conf < min_conf:
            continue
        cls_id = int(box.cls)
        cls_name = results.names[cls_id]
        if cls_name == EXCLUDED_CLASS:
            continue
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        detections.append((
            cls_name,
            int(x1), int(y1), int(x2), int(y2),
            conf
        ))
    return detections

def redimensionar_con_padding(imagen, tamaño_objetivo=(640, 640), color=(114, 114, 114)):
    h, w = imagen.shape[:2]
    escala = min(tamaño_objetivo[0] / h, tamaño_objetivo[1] / w)
    nuevo_w, nuevo_h = int(w * escala), int(h * escala)
    imagen_redimensionada = cv2.resize(imagen, (nuevo_w, nuevo_h), interpolation=cv2.INTER_LINEAR)
    top = (tamaño_objetivo[0] - nuevo_h) // 2
    bottom = tamaño_objetivo[0] - nuevo_h - top
    left = (tamaño_objetivo[1] - nuevo_w) // 2
    right = tamaño_objetivo[1] - nuevo_w - left
    imagen_con_padding = cv2.copyMakeBorder(imagen_redimensionada, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return imagen_con_padding

def init_db():
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (class_name TEXT PRIMARY KEY, product_name TEXT, unit_price REAL)''')
    sample_products = [
        ['toddy-750g', 'Toddy - 750g', 18.5],
        ['yogurt-pil-frutilla-1kg', 'Yogurt Bebible - Pil - 1000g - Frutilla', 10.9],
        ['dulce-leche-pil-500g', 'Dulce de Leche - Pil - 500g', 9.2],
        ['chocolike-800g', 'Chocolike - 800g', 16.3],
        ['chocolike-2000g', 'Chocolike - 2000g', 34.5],
        ['leche-polvo-pil-2200g', 'Leche entera - polvo - Pil - 2200g', 45.0],
        ['leche-condensada-mococa-395g', 'Leche condensada - Mococa - 350g', 6.8],
        ['extracto-tomate-cayetana', 'Extracto de tomate - Cayentana', 4.5],
        ['crema-esparragos-kris-75g', 'Crema de Esparragos - Kris - 75g', 3.7],
        ['crema-champiniones-kris-75g', 'Crema de Champiñones - Kris - 75g', 3.7],
        ['sal-celusal-500g', 'Sal Fina - Celusal - 500g', 2.5],
        ['gelatina-limon-frutigel', 'Gelatina - Limon - Fruti Gel', 1.8],
        ['flan-vainilla-kris-120g', 'Flan - Vainilla - Kris - 120g', 2.6],
        ['mostaza-kris-490g', 'Mostaza - Kris - 490g', 4.3],
        ['mostaza-kris-200g', 'Mostaza - Kris - 200g', 2.7],
        ['ketchup-kris-200g', 'Ketchup - Kris - 200g', 3.2],
        ['ecco-nestle-170g', 'Ecco - Nestle - 170g', 7.8],
        ['te-ciruela-21dias-42u', 'Te - Ciruela - Plan 21 Dias - 42 unidades', 12.5],
        ['choclo-lata-isamar-300g', 'Granos de Choclo - Lata - Isamar - 300g', 4.1],
        ['vainilla-liquida-miki-110ml', 'Vainilla Líquida - Miki - 110ml', 3.9],
    ]
    c.executemany('INSERT OR REPLACE INTO products VALUES (?, ?, ?)', sample_products)
    conn.commit()
    conn.close()

init_db()

model = YOLO(MODEL_PATH)
cart = LayeredShoppingCart()
frame_count = 0
show_occluded = True

@socketio.on('frame')
def handle_frame(data):
    global frame_count, cart
    frame_count += 1
    current_time = time.time()

    # Decode image from base64
    image_data = data['image'].split(',')[1]
    image = Image.open(io.BytesIO(base64.b64decode(image_data)))
    frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    frame_redimensionado = redimensionar_con_padding(frame)

    # Process frame
    changes = {'added': [], 'updated': [], 'removed': [], 'maintained': [], 'occluded': [], 'recovered': []}
    if cart.should_process_frame(frame_count, current_time):
        detections = get_detections(frame_redimensionado, model, MIN_CONF)
        changes = cart.update_cart(detections, current_time)

    # Console output for occluded products
    if show_occluded and frame_count % 10 == 0:
        occluded = [p for p in cart.products.values() if p.state == ProductState.OCCLUDED]
        if occluded:
            print(f"\n--- Productos Ocluidos ({len(occluded)}) ---")
            for product in occluded:
                occlusion_time = current_time - product.occlusion_start
                first_seen_time = current_time - product.first_seen
                print(f"{product.id}: {occlusion_time:.1f}s ocluido, Capa {product.layer}")
                print(f"  Detectado hace: {first_seen_time:.1f}s")
                if product.occluded_by:
                    occluders_info = []
                    for oid in product.occluded_by:
                        if oid in cart.products:
                            occluder = cart.products[oid]
                            occluders_info.append(f"{oid} (Capa {occluder.layer}, Detectado hace {current_time - occluder.first_seen:.1f}s)")
                        else:
                            occluders_info.append(f"{oid} (Temporal)")
                    print(f"  Ocluido por: {', '.join(occluders_info)}")
                else:
                    print(f"  Sin ocluyentes activos")
            print("-" * 25)

    # Console output for cart summary
    summary = cart.get_cart_summary()
    print(f"\n=== Estado Actual del Carrito ===")
    print(f"Productos Visibles ({summary['visible_count']}):")
    for pid, product in summary['visible_products'].items():
        print(f"  - {product.class_name} (ID: {pid}, Capa: {product.layer})")
    print(f"Productos Ocluidos ({summary['occluded_count']}):")
    for pid, product in summary['occluded_products'].items():
        print(f"  - {product.class_name} (ID: {pid}, Capa: {product.layer})")
    print("Productos por Categoría:")
    for class_name, count in summary['class_counts'].items():
        print(f"  - {class_name}: {count} unidad(es)")
    print("=" * 40)

    # Query database and prepare response
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    response = []
    total = 0
    for class_name, quantity in summary['class_counts'].items():
        if quantity > 0:
            c.execute('SELECT product_name, unit_price FROM products WHERE class_name = ?', (class_name,))
            result = c.fetchone()
            if result:
                product_name, unit_price = result
                subtotal = quantity * unit_price
                total += subtotal
                response.append({
                    'product_name': product_name,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'subtotal': subtotal
                })
    conn.close()

    # Emit response to client
    emit('update', {'products': response, 'total': total})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)