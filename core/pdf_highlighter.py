import copy
import difflib
import logging

import fitz

from core.constants import EMPTY_TWO_COLUMN_LEFT_PDF_PATH

logger = logging.getLogger(__name__)


class Box(object):
    def __init__(self, char, page_index, left=None, bottom=None, right=None, top=None, colour=None):
        self.char = char
        self.left = left
        self.bottom = bottom
        self.right = right
        self.top = top
        self.page_index = page_index
        self.colour = colour
        self.active = False

    def get(self):
        return (
            self.left,
            self.bottom,
            self.right,
            self.top,
        )

    def set(self, box):
        self.left, self.bottom, self.right, self.top = box

    def __add__(self, other):
        if self.page_index != other.page_index:
            raise ValueError("Not same page index")
        if self.colour != other.colour:
            raise ValueError("Not same colour")

        box = Box(self.char + other.char, self.page_index, colour=self.colour)
        bbox = (
            min(self.left, other.left),
            min(self.bottom, other.bottom),
            max(self.right, other.right),
            max(self.top, other.top),
        )
        box.set(bbox)
        return box

    def _keys(self):
        return self.page_index, round(self.left), round(self.bottom), round(self.right), round(self.top), self.char

    def __hash__(self):
        return hash(self._keys())

    def __eq__(self, other):
        if self._keys() != other._keys():
            return False
        if self.active != other.active:
            return False
        return True


def add_differ_highlight(new_path, old_path, out_path):
    fitz.TOOLS.mupdf_display_errors(False)
    with fitz.open(new_path, filetype="pdf") as doc_new:
        with fitz.open(old_path, filetype="pdf") as doc_old:

            boxes_new = get_all_boxes(doc_new)
            boxes_old = get_all_boxes(doc_old)
            get_num_sets(boxes_new, boxes_old)

            boxes_new = reduce_boxes(boxes_new)
            boxes_old = reduce_boxes(boxes_old)
            make_annotations(doc_new, boxes_new, boxes_old)
            make_annotations(doc_old, boxes_old, boxes_new)

            with open(EMPTY_TWO_COLUMN_LEFT_PDF_PATH, "rb") as f:
                doc_preset = fitz.Document(stream=f.read(), filetype="pdf")

            for i in range(max(doc_new.page_count, doc_old.page_count)):

                if i >= doc_old.page_count:
                    bound = doc_new[i].bound()
                    doc_preset.new_page(width=bound.x1, height=bound.y1)

                else:
                    doc_preset.insert_pdf(doc_old,
                                         from_page=i,
                                         to_page=i,
                                         annots=True)

                if i >= doc_new.page_count:
                    bound = doc_old[i].bound()
                    doc_preset.new_page(width=bound.x1, height=bound.y1)
                else:
                    doc_preset.insert_pdf(doc_new,
                                         from_page=i,
                                         to_page=i,
                                         annots=True)

            doc_preset.save(out_path,
                            garbage=2,
                            clean=True,
                            deflate=True,
                            pretty=False,
                            ascii=False)


def get_all_boxes(doc):
    boxes = []
    for i, page in enumerate(doc):
        text_page = page.get_textpage()
        blocks = text_page.extractRAWDICT()["blocks"]
        for block in blocks:
            if block["type"] == 1:
                continue
            lines = block["lines"]
            for line in lines:
                spans = line["spans"]
                for span in spans:
                    for char in span["chars"]:
                        if char["c"].strip() == "":
                            continue
                        box = Box(char["c"], i)
                        box.set(char["bbox"])
                        boxes.append(box)
    return boxes


def get_all_text(boxes):
    result = ""
    for box in boxes:
        result += box.char
    return result


def get_num_sets(boxes_new, boxes_old):
    chars_new = get_all_text(boxes_new)
    chars_old = get_all_text(boxes_old)
    seq = difflib.SequenceMatcher(a=chars_new, b=chars_old, autojunk=False)
    last_a = 0
    last_b = 0
    for block in seq.get_matching_blocks():
        if last_a != block.a and last_b != block.b:
            make_box_active(boxes_new, last_a, block.a, [1.0, 1.0, 0.0])
            make_box_active(boxes_old, last_b, block.b, [1.0, 1.0, 0.0])
        elif last_a != block.a and last_b == block.b:
            make_box_active(boxes_new, last_a, block.a, [0.0, 1.0, 0.0])
        elif last_a == block.a and last_b != block.b:
            make_box_active(boxes_old, last_b, block.b, [1.0, 0.0, 0.0])

        last_b = block.b + block.size
        last_a = block.a + block.size


def make_box_active(boxes, first, last, colour):
    for i in range(first, last):
        box = boxes[i]
        box.active = True
        box.colour = colour


def make_annotations(doc, boxes, similar_boxes):
    similar_boxes_set = set(similar_boxes)
    for box in boxes:
        if box in similar_boxes_set:
            continue
        page = doc[box.page_index]
        try:
            annot = page.add_highlight_annot(box.get())
            annot.set_colors(stroke=box.colour)
            annot.update()
        except ValueError as e:  # Bad quads error
            print(f"Error: {e}. Box: {box.get()}")


def reduce_boxes(boxes):
    boxes = filter(lambda box: box.active, boxes)
    reduced_boxes = []
    current_box = None
    for box in boxes:
        if current_box is None:
            current_box = box
            continue

        if box.page_index != current_box.page_index or box.colour != current_box.colour:
            reduced_boxes.append(copy.copy(current_box))
            current_box = box
            continue

        if int(box.top) == int(current_box.top) and \
                int(box.bottom) == int(current_box.bottom) and \
                abs(current_box.right - box.left) <= 5:
            current_box = current_box + box
        else:
            reduced_boxes.append(copy.copy(current_box))
            current_box = box

    if current_box is not None:
        reduced_boxes.append(copy.copy(current_box))

    return reduced_boxes

