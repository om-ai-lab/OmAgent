from PIL import Image
from typing import NamedTuple, List, Optional
import itertools


class ZoomState(NamedTuple):
    """
    Contains the state information for a node in the image tree.
    
    Attributes:
        original_image_pil: Reference to the full original image
        bbox: Bounding box coordinates [x, y, width, height] defining this image region
    """
    original_image_pil: Image.Image
    bbox: List[int]

class Node:
    """
    Represents a node in the hierarchical image tree.
    Each node corresponds to a specific region in the image.
    
    The tree structure enables multi-scale analysis and efficient region-based search.
    """
    id_iter = itertools.count()  # Global counter for generating unique node IDs

    @classmethod
    def reset_id(cls):
        """Reset the global ID counter to start fresh."""
        cls.id_iter = itertools.count()

    def __init__(
        self, 
        state: Optional[ZoomState], 
        parent: "Optional[Node]" = None, 
        fast_confidence: float = None, 
        fast_confidence_details=None, 
        is_terminal: bool = False
    ) -> None:
        """
        Initialize a new node in the image tree.
        
        Args:
            state: Contains image and bbox information for this node
            parent: Reference to parent node (None for root node)
            fast_confidence: Pre-computed confidence score for this region
            fast_confidence_details: Detailed confidence information
            is_terminal: Flag indicating if this is a leaf node that should not be subdivided
        """
        
        self.id = next(Node.id_iter)  # Assign unique ID
        if fast_confidence_details is None:
            fast_confidence_details = {}
        self.confidence_details = {}  # Stores detailed confidence metrics
        self.cum_confidences: list[float] = []  # Cumulative confidence scores
        self.fast_confidence = self.confidence = fast_confidence  # Quick access confidence score
        self.fast_confidence_details = fast_confidence_details  # Detailed breakdown of confidence
        self.answering_confidence = 0  # Confidence that this region answers the query

        self.is_terminal = is_terminal  # Flag to stop further subdivision
        self.state = state  # Image region information
        self.parent = parent  # Reference to parent node
        self.children: 'Optional[list[Node]]' = []  # Child nodes (subdivisions)
        if parent is None:
            self.depth = 0  # Root node has depth 0
        else:
            self.depth = parent.depth + 1  # Child depth is parent depth + 1

    @property
    def is_leaf(self):
        """Check if this node has no children (is a leaf node)."""
        return len(self.children) == 0

    @property
    def is_root(self):
        """Check if this node is the root of the tree."""
        return self.depth == 0

    def add_child(self, child: 'Node'):
        """Add a child node to this node's children list."""
        self.children.append(child)
    
    def save_crop(self, path):
        """
        Save the image region corresponding to this node to a file.
        Useful for debugging and visualization.
        
        Args:
            path: File path where the cropped image should be saved
        """
        x, y, w, h = self.state.bbox
        crop_image = self.state.original_image_pil.crop([x, y, x+w, y+h])
        crop_image.save(path)

def is_terminal(node: Node, smallest_size: int) -> bool:
    """
    Determine if a node should be considered terminal (not further subdivided).
    A node is terminal if its width or height is smaller than smallest_size.
    
    Args:
        node: The node to check
        smallest_size: Minimum dimension threshold
        
    Returns:
        bool: True if the node should not be subdivided further
    """
    now_w, now_h = node.state.bbox[2:]
    return max(now_w, now_h) < smallest_size

class ImageTree:
    """
    Hierarchical representation of an image for multi-scale analysis.
    Divides the image into progressively smaller regions in a quad-tree like structure.
    """
    def __init__(self, image_pil, patch_size):
        """
        Initialize the image tree with the original image.
        
        Args:
            image_pil: The original PIL image
            patch_size: Minimum size of image patches (termination condition)
        """
        self.image_pil = image_pil
        self.patch_size = patch_size
        # Create root node covering the entire image
        self.root = Node(ZoomState(image_pil, [0, 0, image_pil.width, image_pil.height]))
        self.max_depth = 0  # Track the maximum depth of the tree
        self._build()  # Build the entire tree structure
        
    
    def _build(self):
        """Build the entire image tree starting from the root."""
        self._build_recursive(self.root)
    
    def _build_recursive(self, node: Node):
        """
        Recursively build the image tree by subdividing nodes.
        
        Args:
            node: Current node to potentially subdivide
        """
        self.max_depth = max(self.max_depth, node.depth)  # Update max depth tracker
        if is_terminal(node, self.patch_size):
            return  # Stop subdivision if node is too small
            
        # Get subdivision strategy and create sub-patches
        sub_patches, _, _ = get_sub_patches(node.state.bbox, *split_4subpatches(node.state.bbox))
        for sub_patch in sub_patches:   
            # Create a new state for each sub-patch
            next_state = ZoomState(
                original_image_pil=node.state.original_image_pil,
                bbox=sub_patch,
            )
            # Add child node with the new state
            node.add_child(Node(
                state=next_state,
                parent=node,
            ))

        # Recursively process each child node
        for child in node.children:
            self._build_recursive(child)


def get_sub_patches(current_patch_bbox, num_of_width_patches, num_of_height_patches):
    """
    Divide a rectangular region into a grid of sub-patches.
    
    Args:
        current_patch_bbox: Current bounding box [x, y, width, height]
        num_of_width_patches: Number of divisions along width
        num_of_height_patches: Number of divisions along height
        
    Returns:
        tuple: (list of sub-patch bboxes, width stride, height stride)
    """
    width_stride = int(current_patch_bbox[2]//num_of_width_patches)
    height_stride = int(current_patch_bbox[3]/num_of_height_patches)
    sub_patches = []
    for j in range(num_of_height_patches):
        for i in range(num_of_width_patches):
            # Handle edge case where division isn't even
            sub_patch_width = current_patch_bbox[2] - i*width_stride if i == num_of_width_patches-1 else width_stride
            sub_patch_height = current_patch_bbox[3] - j*height_stride if j == num_of_height_patches-1 else height_stride
            # Calculate coordinates for this sub-patch
            sub_patch = [current_patch_bbox[0]+i*width_stride, current_patch_bbox[1]+j*height_stride, sub_patch_width, sub_patch_height]
            sub_patches.append(sub_patch)
    return sub_patches, width_stride, height_stride

def split_4subpatches(current_patch_bbox):
    """
    Determine the optimal way to split a patch based on its aspect ratio.
    Maintains reasonable aspect ratios in the resulting sub-patches.
    
    Args:
        current_patch_bbox: Current bounding box [x, y, width, height]
        
    Returns:
        tuple: (width_divisions, height_divisions)
    """
    hw_ratio = current_patch_bbox[3] / current_patch_bbox[2]
    if hw_ratio >= 2:
        # Very tall rectangle: split into 4 vertical sections
        return 1, 4
    elif hw_ratio <= 0.5:
        # Very wide rectangle: split into 4 horizontal sections
        return 4, 1
    else:
        # Near-square region: split into 2×2 grid
        return 2, 2
