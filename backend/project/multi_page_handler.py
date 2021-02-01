import logging
from pathlib import Path

from PIL import Image, TiffTags
from PIL.TiffImagePlugin import AppendingTiffWriter
from PIL import TiffImagePlugin
from pdf2image import convert_from_path

TiffTags.LIBTIFF_CORE.add(317)
TiffImagePlugin.WRITE_LIBTIFF = True
Image.MAX_IMAGE_PIXELS = 1_000_000_000
logger = logging.getLogger("flax_task")


class MultiPageHandler:
    """ An utility to handle multiple-page files
    """

    def __init__(self, folder_path=None):
        """
        :param folder_path: absolute path to media folder.
        Folders with only tif/tiff and pdf files are highly recommended
        """
        self.temp_files = set()
        self.temp_path = None
        if folder_path is None:
            self.path = None
        else:
            self.path = Path(folder_path).resolve()

    def process_single_file(self, input_path, temp_path):
        try:
            _input_path = Path(input_path)

            self.path = _input_path.parent
            self.temp_path = Path(temp_path)
            extension = _input_path.suffix.lower()

            if extension == ".pdf":
                temp_list = self._convert_pdf_file([_input_path])
            elif extension == ".tiff" or extension == ".tif":
                temp_list = self._convert_tiff_file([_input_path])
            else:
                return []

            self.temp_files.update(temp_list)

            return sorted(list(self.temp_files))
        except Exception:
            import traceback
            logger.error(traceback.format_exc())

            return []

    def process_all(self):
        """Convert any multiple-page images within the folder to single ones.
        Ex: for filename sample.tiff
        - If it has 1 page, a file named sample_0.png is created
        - If it has 2 pages, files named sample_0.png and sample_1.png
        are created
        :return: list of absolute path to temporary files
        """
        if self.path is None:
            raise ValueError("Path to images is currently not set.")

        pdf_file_list = list(self.path.glob("*.pdf"))
        pdf_temp_list = self._convert_pdf_file(pdf_file_list)
        self.temp_files.update(pdf_temp_list)

        tiff_file_list = list(self.path.glob("*.tif")) + list(self.path.glob("*.tiff"))
        tiff_temp_list = self._convert_tiff_file(tiff_file_list)
        self.temp_files.update(tiff_temp_list)

        return sorted(list(self.temp_files))

    def _convert_pdf_file(self, file_list):
        """Handle multiple-page pdf.
        :param file_list: list of file names
        :return: list of absolute path to temporary files
        """
        pdf_temp_list = []
        if not self.temp_path.is_dir():
            self.temp_path.mkdir(parents=True)
        for file_name in file_list:
            images = convert_from_path(str(file_name), thread_count=4, dpi=200)

            for i, img in enumerate(images):
                name = "{}_{}.png".format(file_name.stem, i)
                save_path = str(Path(self.temp_path, name))
                img.save(save_path, dpi=(300, 300))
                pdf_temp_list.append(save_path)

        return pdf_temp_list

    def _convert_tiff_file(self, file_list):
        """Handle multiple-page tiff/tif images.
        :param file_list: list of file names
        :return: list of absolute path to temporary files
        """
        tiff_temp_list = []

        for file_name in file_list:
            img = Image.open(str(file_name))

            for i in range(img.n_frames):
                try:
                    img.seek(i)
                    name = "{}_{}.png".format(file_name.stem, i)
                    save_path = str(Path(self.path, name))
                    img.save(save_path, dpi=(300, 300))

                    tiff_temp_list.append(save_path)
                except EOFError:
                    break

        return tiff_temp_list

    def export_tiff_file(self, save_path):
        with AppendingTiffWriter(str(save_path), True) as tf:
            for png_in in self.temp_files:
                with open(png_in, 'rb') as png_in:
                    im = Image.open(png_in)
                    im.save(tf, compression='tiff_lzw', tiffinfo={317: 2})
                    tf.newFrame()

    def clean_temp_files(self):
        """Clean all temporary files in folder."""

        while self.temp_files:
            temp_file = self.temp_files.pop()
            Path(temp_file).unlink()
