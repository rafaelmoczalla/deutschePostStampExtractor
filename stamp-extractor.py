#!/usr/bin/env python3

__description__ = "stamp-extractor, use it to extract german stamps from downloaded pdf stamp from shop.deutschepost.de"
__author__ = "Rafael Moczalla"
__version__ = "0.1.0"
__date__ = "2021/11/26"
__minimum_python_version__ = (3, 6, 0)
__maximum_python_version__ = (3, 9, 7)

import sys
import glob
import fitz
import io
import os
import numpy as np
from PIL import Image
import cairo
import gi
gi.require_version("Rsvg", "2.0")
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Rsvg, Pango, PangoCairo
import manimpango


def extractQRCode(pdf_file):
  images = []

  # iterate over PDF pages
  for page_index in range(len(pdf_file)):

    # get the page itself
    page = pdf_file[page_index]
    image_list = page.get_images()

    # printing number of images found in this page
    if image_list:
      print(f"[+] Found a total of {len(image_list)} images in page {page_index}")
    else:
      print("[!] No images found on page", page_index)

    for image_index, img in enumerate(page.get_images(), start=1):

      # get the XREF of the image
      xref = img[0]

      # extract the image bytes
      base_image = pdf_file.extract_image(xref)
      image_bytes = base_image["image"]

      images.append(Image.open(io.BytesIO(image_bytes)))

  return images

def extractLabels(pdf_file):
  labels = []

  # iterate over PDF pages
  for page_index in range(len(pdf_file)):

    # get the page itself
    page = pdf_file[page_index]
    image_list = page.get_text("blocks", sort=False)

    # printing number of labels found in this page
    if image_list:
      print(f"[+] Found a total of {len(image_list)} text lines in page {page_index}")
    else:
      print("[!] No text lines found on page", page_index)

    labels = [*labels, *image_list]

  return labels

def createStamp(nr, qr, textLines, scale, width, height):
  handle = Rsvg.Handle()

  surface = cairo.PDFSurface("qr" + str(nr) + ".pdf", width, height)
  # creating a cairo context object
  context = cairo.Context(surface)

  # Deutsche Post label
  label = handle.new_from_file("label.svg")
  dimLabel = label.get_dimensions()
  rect = Rsvg.Rectangle()
  rect.x = 0
  rect.y = 0
  rect.width = width
  rect.height = dimLabel.height * width / dimLabel.width
  label.render_document(context, rect)

  # IM label
  im = handle.new_from_file("im.svg")
  dimIm = im.get_dimensions()
  rect.x = scale*1
  rect.y = scale*25.5
  rect.width = dimIm.width * width / dimLabel.width
  rect.height = dimIm.height * width / dimLabel.width
  im.render_document(context, rect)

  # QR code
  qrarr = np.asarray(qr)
  x = len(qrarr) / 26.0 / 2.0
  xi = 0
  while x < len(qrarr):
    y = len(qrarr[0]) / 26.0 / 2.0
    yi = 0
    while y < len(qrarr[0]):
      if qrarr[int(y)][int(x)] == 0:
        context.rectangle(
            0 + float(xi) * float(width) / 26.0 - 0.05,
            float(scale*44) + float(yi) * float(width) / 26.0 - 0.05,
            float(width) / 26.0 + float(scale) * 0.05,
            float(width) / 26.0 + float(scale) * 0.05)
        context.fill()
      yi += 1
      y = len(qrarr[0]) / 26.0 / 2.0 + yi * len(qrarr[0]) / 26.0
    xi += 1
    x = len(qrarr) / 26.0 / 2.0 + xi *len(qrarr) / 26.0

  # Drawing code
  manimpango.register_font("ayar.ttf")
  manimpango.register_font("NotoMono-Regular.ttf")

  # date
  line = textLines[0][4]
  line = line[3:-1]
  price = line.split("\n")
  date = price[0]

  context.move_to(scale*25, scale*21)

  layout = PangoCairo.create_layout(context)
  font = Pango.FontDescription("Ayar 46")
  layout.set_font_description(font)

  layout.set_text(date)

  PangoCairo.show_layout(context, layout)

  # price
  price = price[1]

  context.move_to(scale*130, scale*21)
  layout = PangoCairo.create_layout(context)
  layout.set_width(width)
  layout.set_alignment(Pango.Alignment.RIGHT)
  font = Pango.FontDescription("Ayar 46")
  layout.set_font_description(font)

  layout.set_text(price)

  PangoCairo.show_layout(context, layout)

  # ID
  line = textLines[1][4]
  line = line[:-1]

  context.move_to(scale*0.5, scale*177)

  layout = PangoCairo.create_layout(context)
  font = Pango.FontDescription("Noto Mono 54")
  layout.set_line_spacing(0.9)# + layout.get_height())
  layout.set_font_description(font)

  layout.set_text(line)

  PangoCairo.show_layout(context, layout)

def Main():
  """stamp-extractor, use it to extract german stamps from pdf
  """
  # search for post stamp file
  file = "Briefmarken.pdf"
  for file in os.listdir():
    if file.startswith("Briefmarke"):
      break

  # delete old stamps from folder
  for filename in glob.glob("qr*"):
    os.remove(filename)

  # open the file
  pdf_file = fitz.open(file)
  qrs = extractQRCode(pdf_file)
  textLines = extractLabels(pdf_file)

  # create stamps
  scale = 4
  width = scale*130
  height = scale*214

  i = 0
  j = 0

  while i < len(qrs):
    createStamp(i, qrs[i], textLines[j:j+3], scale, width, height)
    i += 1
    j += 3

def TestPythonVersion(enforceMaximumVersion=False, enforceMinimumVersion=False):
  if sys.version_info[0:3] > __maximum_python_version__:
    if enforceMaximumVersion:
      print("This program does not work with this version of Python (%d.%d.%d)" % sys.version_info[0:3])
      print("Please use Python version %d.%d.%d" % __maximum_python_version__)
      sys.exit()
    else:
      print("This program has not been tested with this version of Python (%d.%d.%d)" % sys.version_info[0:3])
      print("Should you encounter problems, please use Python version %d.%d.%d" % __maximum_python_version__)
  if sys.version_info[0:3] < __minimum_python_version__:
    if enforceMinimumVersion:
      print("This program does not work with this version of Python (%d.%d.%d)" % sys.version_info[0:3])
      print("Please use Python version %d.%d.%d" % __maximum_python_version__)
      sys.exit()
    else:
      print("This program has not been tested with this version of Python (%d.%d.%d)" % sys.version_info[0:3])
      print("Should you encounter problems, please use Python version %d.%d.%d" % __maximum_python_version__)

if __name__ == "__main__":
  TestPythonVersion()
  Main()
