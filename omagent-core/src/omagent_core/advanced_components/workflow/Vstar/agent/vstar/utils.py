import spacy
nlp = spacy.load("en_core_web_sm")
MISSING_INFO = "Sorry, I can not answer the question. Some visual information about the following objects is missing or unclear:"

CONFIDENCE_HIGH = 0.5
CONFIDENCE_LOW = 0.3
TARGET_CUE_THRESHOLD = 6.0
TARGET_CUE_THRESHOLD_DECAY = 0.7
TARGET_CUE_THRESHOLD_MINIMUM = 3.0
SMALLEST_SIZE = 224
MAX_SEARCH_STEP = 10

def tranverse(token):
	children = [_ for _ in token.children]
	if len(children) == 0:
		return token.i, token.i
	left_i = token.i
	right_i = token.i
	for child in children:
		child_left_i, child_right_i = tranverse(child)
		left_i = min(left_i, child_left_i)
		right_i = max(right_i, child_right_i)
	return left_i, right_i

def get_noun_chunks(token):
	left_children = []
	right_children = []
	for child in token.children:
		if child.i < token.i:
			left_children.append(child)
		else:
			right_children.append(child)

	start_token_i = token.i
	for left_child in left_children[::-1]:
		if left_child.dep_ in ['amod', 'compound', 'poss']:
			start_token_i, _ = tranverse(left_child)
		else:
			break
	end_token_i = token.i
	for right_child in right_children:
		if right_child.dep_ in ['relcl', 'prep']:
			_, end_token_i = tranverse(right_child)
		else:
			break
	return start_token_i, end_token_i

def filter_chunk_list(chunks):
	def overlap(min1, max1, min2, max2):
		return min(max1, max2) - max(min1, min2)
	chunks = sorted(chunks, key=lambda chunk: chunk[1]-chunk[0], reverse=True)
	filtered_chunks = []
	for chunk in chunks:
		flag=True
		for exist_chunk in filtered_chunks:
			if overlap(exist_chunk[0], exist_chunk[1], chunk[0], chunk[1]) >= 0:
				flag = False
				break
		if flag:
			filtered_chunks.append(chunk)
	return sorted(filtered_chunks, key=lambda chunk: chunk[0])

def extract_noun_chunks(expression):
	doc = nlp(expression)
	cur_chunks = []
	for token in doc:
		if token.pos_ not in ["NOUN", "PRON"]:
			continue
		cur_chunks.append(get_noun_chunks(token))
	cur_chunks = filter_chunk_list(cur_chunks)
	cur_chunks = [doc[chunk[0]:chunk[1]+1].text for chunk in cur_chunks]
	return cur_chunks

def get_sub_patches(current_patch_bbox, num_of_width_patches, num_of_height_patches):
	width_stride = int(current_patch_bbox[2]//num_of_width_patches)
	height_stride = int(current_patch_bbox[3]/num_of_height_patches)
	sub_patches = []
	for j in range(num_of_height_patches):
		for i in range(num_of_width_patches):
			sub_patch_width = current_patch_bbox[2] - i*width_stride if i == num_of_width_patches-1 else width_stride
			sub_patch_height = current_patch_bbox[3] - j*height_stride if j == num_of_height_patches-1 else height_stride
			sub_patch = [current_patch_bbox[0]+i*width_stride, current_patch_bbox[1]+j*height_stride, sub_patch_width, sub_patch_height]
			sub_patches.append(sub_patch)
	return sub_patches, width_stride, height_stride

def split_4subpatches(current_patch_bbox):
	hw_ratio = current_patch_bbox[3] / current_patch_bbox[2]
	if hw_ratio >= 2:
		return 1, 4
	elif hw_ratio <= 0.5:
		return 4, 1
	else:
		return 2, 2

def get_subpatch_scores(score_heatmap, current_patch_bbox, sub_patches):
	total_sum = (score_heatmap/(current_patch_bbox[2]*current_patch_bbox[3])).sum()
	sub_scores = []
	for sub_patch in sub_patches:
		bbox = [(sub_patch[0]-current_patch_bbox[0]), sub_patch[1]-current_patch_bbox[1], sub_patch[2], sub_patch[3]]
		score = (score_heatmap[bbox[1]:bbox[1]+bbox[3], bbox[0]:bbox[0]+bbox[2]]/(current_patch_bbox[2]*current_patch_bbox[3])).sum()
		if total_sum > 0:
			score /= total_sum
		else:
			score *= 0
		sub_scores.append(score)
	return sub_scores


import functools

@functools.total_ordering
class Prioritize:

	def __init__(self, priority, item):
		self.priority = priority
		self.item = item

	def __eq__(self, other):
		return self.priority == other.priority

	def __lt__(self, other):
		return self.priority < other.priority