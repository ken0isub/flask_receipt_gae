import datetime
import cv2
from enum import Enum
import re

def read_costco(response):
    costco_lines = response.text_annotations[0].description.rsplit()
    total_price = costco_lines[costco_lines.index('合計') + 1].replace(',', '').replace('.', '')
    buy_date = [s for s in costco_lines if re.match(r'\d+/\d+/\d+', s)][0]
    date_dt = datetime.datetime.strptime(buy_date, '%m/%d/%y')
    date_dt = date_dt.strftime('%Y/%m/%d')
    return total_price, date_dt

def read_seven(response):
    seven_lines = response.text_annotations[0].description.splitlines()
    seven_total_item = [s for s in seven_lines if s.startswith(('合 計', '合計'))][0]
    seven_total = re.sub(r"\D", "", seven_total_item)
    if seven_total == '':
        seven_total_item = seven_lines[seven_lines.index(seven_total_item) + 1]
        seven_total = re.sub(r"\D", "", seven_total_item)
    buy_date = [s for s in seven_lines if re.match(r'\d+年\d+月\d+日', s)][0][:11]
    date_dt = datetime.datetime.strptime(buy_date, '%Y年%m月%d日')
    date_dt = date_dt.strftime('%Y/%m/%d')
    return seven_total, date_dt


#read_lawson can read familymart as well
def read_lawson(response):
    lines = response.text_annotations[0].description.splitlines()
    total_item = [s for s in lines if s.startswith(('合 計', '合計', '・計'))][0]
    total = re.sub(r"\D", "", total_item)
    if total == '':
        total_item = lines[lines.index(total_item) + 1]
        total = re.sub(r"\D", "", total_item)
    buy_date = [s for s in lines if re.match(r'\d+年.*\d+月.*\d+日', s)][0]
    buy_date = buy_date[:buy_date.index('(')].replace(' ', '')
    date_dt = datetime.datetime.strptime(buy_date, '%Y年%m月%d日')
    date_dt = date_dt.strftime('%Y/%m/%d')
    return total, date_dt


def read_kasumi(response):
    lines = response.text_annotations[0].description.splitlines()
    try:
        total_item = [s for s in lines if s.startswith(('ご利用金額'))][0]
        total = re.sub(r"\D", "", total_item)
        if total == '':
            total_item = [s for s in lines if s.startswith(('ご利用金額'))][0]
            total_item = lines[lines.index(total_item) + 1]
            total = re.sub(r"\D", "", total_item)
    except IndexError:
        total = 'couldn\'t get'
    try:
        find_total = [s for s in lines if s.startswith(('合計'))][0]
        discount = lines[lines.index(find_total) - 4]
        if discount.startswith('-'):
            discount = re.sub(r"\D", "", discount)
        else:
            discount = "0"
    except IndexError:
        discount = "0"
    try:
        find_coupon = [s for s in lines if s.endswith(('券'))][0]
        coupon_discount = lines[lines.index(find_coupon) + 3]
        if coupon_discount.startswith('-'):
            coupon_discount = re.sub(r"\D", "", coupon_discount)
        else:
            coupon_discount = "0"
    except IndexError:
        coupon_discount = "0"
    total_discount = int(discount) + int(coupon_discount)
    buy_date = [s for s in lines if re.match(r'\d+年.*\d+月.*\d+日', s)][0]
    try:
        buy_date = buy_date[:buy_date.index('(')].replace(' ', '')
        date_dt = datetime.datetime.strptime(buy_date, '%Y年%m月%d日')
        date_dt = date_dt.strftime('%Y/%m/%d')
    except ValueError:
        date_dt = datetime.datetime.strptime(buy_date, '%y年%m月%d日')
        date_dt = date_dt.strftime('%Y/%m/%d')
    except:
        date_dt = 'couldn\'t get'
    return total, date_dt, total_discount


def draw_boxes(input_file, bounds):
    img = cv2.imread(input_file, cv2.IMREAD_COLOR)
    for bound in bounds:
      p1 = (bound.vertices[0].x, bound.vertices[0].y) # top left
      p2 = (bound.vertices[1].x, bound.vertices[1].y) # top right
      p3 = (bound.vertices[2].x, bound.vertices[2].y) # bottom right
      p4 = (bound.vertices[3].x, bound.vertices[3].y) # bottom left
      cv2.line(img, p1, p2, (0, 255, 0), thickness=1, lineType=cv2.LINE_AA)
      cv2.line(img, p2, p3, (0, 255, 0), thickness=1, lineType=cv2.LINE_AA)
      cv2.line(img, p3, p4, (0, 255, 0), thickness=1, lineType=cv2.LINE_AA)
      cv2.line(img, p4, p1, (0, 255, 0), thickness=1, lineType=cv2.LINE_AA)
    return img


class FeatureType(Enum):
    PAGE = 1
    BLOCK = 2
    PARA = 3
    WORD = 4
    SYMBOL = 5



def get_document_bounds(response, feature):
    document = response.full_text_annotation
    bounds = []
    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    for symbol in word.symbols:
                        if (feature == FeatureType.SYMBOL):
                          bounds.append(symbol.bounding_box)
                    if (feature == FeatureType.WORD):
                        bounds.append(word.bounding_box)
                if (feature == FeatureType.PARA):
                    bounds.append(paragraph.bounding_box)
            if (feature == FeatureType.BLOCK):
                bounds.append(block.bounding_box)
    return bounds


def get_sorted_lines(response):
    document = response.full_text_annotation
    bounds = []
    for page in document.pages:
      for block in page.blocks:
        for paragraph in block.paragraphs:
          for word in paragraph.words:
            for symbol in word.symbols:
              x = symbol.bounding_box.vertices[0].x
              y = symbol.bounding_box.vertices[0].y
              text = symbol.text
              bounds.append([x, y, text, symbol.bounding_box])
    bounds.sort(key=lambda x: x[1])
    old_y = -1
    line = []
    lines = []
    threshold = 1
    for bound in bounds:
      x = bound[0]
      y = bound[1]
      if old_y == -1:
        old_y = y
      elif old_y-threshold <= y <= old_y+threshold:
        old_y = y
      else:
        old_y = -1
        line.sort(key=lambda x: x[0])
        lines.append(line)
        line = []
      line.append(bound)
    line.sort(key=lambda x: x[0])
    lines.append(line)
    return lines