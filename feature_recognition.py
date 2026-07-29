import numpy as np
import trimesh

def segment_mesh_features(mesh, angle_threshold_degrees=30.0):
    """
    Segments a trimesh into features (flat faces, cylinders/holes, etc.)
    by grouping adjacent faces with normal angles below a threshold.
    """
    # Convert threshold to radians
    threshold_rad = np.radians(angle_threshold_degrees)
    
    # 1. Get face adjacency and the angles between adjacent faces
    adjacency = mesh.face_adjacency
    angles = mesh.face_adjacency_angles
    
    # 2. Filter adjacency edges where the angle is below the threshold
    # This will group faces that transition smoothly (e.g. cylinder panels, flat regions)
    # but separate sharp edges (like the 90-degree transition to end-caps)
    valid_edges = adjacency[angles < threshold_rad]
    
    # 3. Find connected components of faces
    components = trimesh.graph.connected_components(valid_edges, min_len=1)
    
    return components

def analyze_cylindrical_surface(mesh, face_indices):
    """
    Fits a cylinder to a subset of faces from a trimesh using normal vector analysis (SVD)
    and 2D least-squares circle fitting.
    """
    if len(face_indices) < 3:
        return None
    
    # 1. Get face normals and vertices
    normals = mesh.face_normals[face_indices]
    
    # 2. Find the cylinder axis using SVD on face normals
    U, S, Vt = np.linalg.svd(normals)
    axis = Vt[-1] # The last row of Vt is the eigenvector of the smallest eigenvalue
    axis = axis / np.linalg.norm(axis) # Ensure unit vector
    
    # 3. Rotate the vertices so that the cylinder axis aligns with the Z-axis [0, 0, 1]
    z_axis = np.array([0.0, 0.0, 1.0])
    if np.allclose(axis, z_axis):
        R = np.eye(3)
    elif np.allclose(axis, -z_axis):
        R = np.diag([1.0, -1.0, -1.0])
    else:
        v = np.cross(axis, z_axis)
        s = np.linalg.norm(v)
        c = np.dot(axis, z_axis)
        vx = np.array([[0, -v[2], v[1]],
                       [v[2], 0, -v[0]],
                       [-v[1], v[0], 0]])
        R = np.eye(3) + vx + np.dot(vx, vx) * ((1 - c) / (s ** 2))
        
    # Get all unique vertices belonging to these faces
    unique_vertex_indices = np.unique(mesh.faces[face_indices])
    vertices = mesh.vertices[unique_vertex_indices]
    
    # Rotate vertices
    rotated_vertices = np.dot(vertices, R.T)
    
    # 4. Project onto the 2D XY-plane and fit a circle
    xy_points = rotated_vertices[:, :2]
    
    # Least squares circle fitting: (x - xc)^2 + (y - yc)^2 = R^2
    A = np.column_stack([xy_points, np.ones(len(xy_points))])
    B = np.sum(xy_points**2, axis=1)
    
    try:
        C, residuals, rank, s = np.linalg.lstsq(A, B, rcond=None)
        xc, yc = C[0] / 2.0, C[1] / 2.0
        r2_minus_xc2_yc2 = C[2]
        r = np.sqrt(r2_minus_xc2_yc2 + xc**2 + yc**2)
    except Exception as e:
        return None
    
    # 5. Map 2D center back to 3D space
    center_rotated = np.array([xc, yc, np.mean(rotated_vertices[:, 2])])
    center_3d = np.dot(center_rotated, R) # Since R is orthogonal, inverse rotation is R.T, so to go back: point * R
    
    # 6. Verify fit quality (calculate distance of vertices from axis)
    cross_products = np.cross(vertices - center_3d, axis)
    distances = np.linalg.norm(cross_products, axis=1)
    mean_error = np.mean(np.abs(distances - r))
    max_error = np.max(np.abs(distances - r))
    
    # 7. Check if it's an internal cylinder (hole) or external cylinder (boss)
    face_centroids = mesh.triangles_center[face_indices]
    t = np.dot(face_centroids - center_3d, axis)
    projections = center_3d + np.outer(t, axis)
    outward_vectors = face_centroids - projections
    outward_vectors /= np.linalg.norm(outward_vectors, axis=1, keepdims=True)
    
    # Dot product with face normals
    dot_products = np.sum(normals * outward_vectors, axis=1)
    is_hole = np.mean(dot_products) < 0.0 # If normals point inward, it's a hole
    
    return {
        "axis": axis,
        "center": center_3d,
        "radius": r,
        "mean_error": mean_error,
        "max_error": max_error,
        "is_hole": is_hole,
        "height": np.max(rotated_vertices[:, 2]) - np.min(rotated_vertices[:, 2])
    }

if __name__ == "__main__":
    print("Testing cylinder detection with segmentation...")
    mesh = trimesh.creation.cylinder(radius=5.0, height=20.0)
    
    # Segment the mesh using our angle threshold algorithm
    components = segment_mesh_features(mesh, angle_threshold_degrees=30.0)
    print(f"Total components found: {len(components)}")
    
    for i, comp in enumerate(components):
        # We can distinguish flat components from curved ones
        # A component is perfectly flat if the max angle between any of its face normals is near 0
        normals = mesh.face_normals[comp]
        # Calculate dot products of all normals with the first one
        dots = np.dot(normals, normals[0])
        # If all dot products are very close to 1.0, it's a flat face
        is_flat = np.all(dots > 0.999)
        
        area = mesh.area_faces[comp].sum()
        
        if is_flat:
            normal = normals[0]
            print(f"Component {i}: Flat Face")
            print(f"  Area: {area:.2f}, Face Count: {len(comp)}")
            print(f"  Normal: {normal}")
        else:
            # Let's try to fit a cylinder to the non-flat component
            result = analyze_cylindrical_surface(mesh, comp)
            if result and result["mean_error"] < 0.1: # Threshold for cylinder fit
                feature_type = "Hole" if result["is_hole"] else "Boss/Outer Cylinder"
                print(f"Component {i}: Cylindrical {feature_type}")
                print(f"  Center: {result['center']}")
                print(f"  Axis: {result['axis']}")
                print(f"  Radius: {result['radius']:.4f} (Expected=5.0)")
                print(f"  Height: {result['height']:.4f}")
                print(f"  Mean Fit Error: {result['mean_error']:.2e}")
            else:
                print(f"Component {i}: Complex Curved Surface")
                print(f"  Area: {area:.2f}, Face Count: {len(comp)}")
