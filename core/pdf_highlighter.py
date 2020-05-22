import difflib
import io

import PyPDF2
import fitz

COLOUR_PALLET = [
    [1.0, 1.0, 0.0],
    [0.0, 1.0, 0.0],
]


def add_differ_highlight(new_path, old_path):
    with fitz.open(new_path) as doc_new:
        with fitz.open(old_path) as doc_old:
            chars_new = get_all_text(doc_new)
            chars_old = get_all_text(doc_old)
            set_a, set_a_only, set_b, set_b_only = get_num_sets(chars_new, chars_old)

            make_annotations(doc_new, set_a, set_a_only)
            make_annotations(doc_old, set_b, set_b_only)

            f_a = doc_new.write()
            f_b = doc_old.write()
            pdf_a = PyPDF2.PdfFileReader(io.BytesIO(f_a))
            pdf_b = PyPDF2.PdfFileReader(io.BytesIO(f_b))

    output_pdf = PyPDF2.PdfFileWriter()
    for i in range(max(pdf_a.getNumPages(), pdf_b.getNumPages())):
        try:
            page_b = pdf_b.getPage(i)
            output_pdf.addPage(page_b)
        except IndexError:
            output_pdf.addBlankPage()

        try:
            page_a = pdf_a.getPage(i)
            output_pdf.addPage(page_a)
        except IndexError:
            output_pdf.addBlankPage()

    output_pdf.setPageLayout("/TwoColumnLeft")
    with open(old_path, "wb") as f:
        output_pdf.write(f)


def get_char_from_blocks(blocks):
    for block in blocks:
        lines = block["lines"]
        for line in lines:
            spans = line["spans"]
            for span in spans:
                for char in span["chars"]:
                    yield char


def get_all_text(doc):
    result = ""
    for page in doc:
        text_page = page.getTextPage()
        blocks = text_page.extractRAWDICT()["blocks"]
        for char in get_char_from_blocks(blocks):
            result += char["c"]
    return result


def get_num_sets(chars_new, chars_old):
    seq = difflib.SequenceMatcher(a=chars_new, b=chars_old, autojunk=False)
    last_a = 0
    last_b = 0
    set_a = set([])
    set_a_only = set([])
    set_b = set([])
    set_b_only = set([])
    for block in seq.get_matching_blocks():
        if last_a != block.a and last_b != block.b:
            set_a.update(set(range(last_a+1, block.a+1)))
            set_b.update(set(range(last_b+1, block.b+1)))
        elif last_a != block.a and last_b == block.b:
            set_a_only.update(set(range(last_a+1, block.a+1)))
        elif last_a == block.a and last_b != block.b:
            set_b_only.update(set(range(last_b+1, block.b+1)))

        last_b = block.b + block.size
        last_a = block.a + block.size

    return set_a, set_a_only, set_b, set_b_only


def make_annotations(doc, *args):
    count = 0
    for page in doc:
        text_page = page.getTextPage()
        blocks = text_page.extractRAWDICT()["blocks"]
        last_boxes = [None for _ in range(len(args))]
        boxes_in_boxes = [[] for _ in range(len(args))]
        for char in get_char_from_blocks(blocks):
            box = char["bbox"]
            for i, (boxes, valid_count) in enumerate(zip(boxes_in_boxes, args)):
                if count in valid_count:
                    last_boxes[i] = check_box(last_boxes[i], box, boxes)
                    break
                elif last_boxes[i] is not None:
                    boxes.append(last_boxes[i])
                    last_boxes[i] = None
            count += 1

        for i, (boxes, valid_count) in enumerate(zip(boxes_in_boxes, args)):
            if last_boxes[i] is not None:
                boxes.append(last_boxes[i])
                last_boxes[i] = None
        for i, boxes in enumerate(boxes_in_boxes):
            for box in boxes:
                colour = COLOUR_PALLET[i]
                annot = page.addHighlightAnnot(box)
                annot.setColors(stroke=colour)
                annot.update()


def check_box(last_box, box, boxes):
    if last_box is None:
        return box
    if box[1] == last_box[1] and box[3] == last_box[3] and abs(last_box[2] - box[0]) < 1:
        return (
            min(box[0], last_box[0]),
            box[1],
            max(box[2], last_box[2]),
            box[3]
        )
    boxes.append(last_box)
    return box
