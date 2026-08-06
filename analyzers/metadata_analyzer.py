import os
import time
import fitz  # PyMuPDF

from PIL import Image, ExifTags

from core.analysis_result import AnalysisResult
from core.evidence import Evidence


class MetadataAnalyzer:


    def analyze(self, file_path):

        start = time.time()

        try:

            extension = os.path.splitext(file_path)[1].lower()

            evidences = []
            score = 0


            if extension == ".pdf":

                data, evidences = self._analyze_pdf(file_path)


            elif extension in [".jpg", ".jpeg", ".png"]:

                data, evidences = self._analyze_image(file_path)


            else:

                return AnalysisResult(
                    success=False,
                    module="metadata",
                    warnings=[
                        "Formato de arquivo não suportado."
                    ]
                )


            # soma dos pesos das evidências

            for evidence in evidences:
                score += evidence.weight


            return AnalysisResult(

                success=True,

                module="metadata",

                score=score,

                data=data,

                evidences=evidences,

                execution_time=time.time() - start

            )


        except Exception as e:


            return AnalysisResult(

                success=False,

                module="metadata",

                warnings=[
                    str(e)
                ]

            )



    def _analyze_pdf(self, file_path):


        pdf = fitz.open(file_path)

        metadata = pdf.metadata


        evidences = []


        # Verifica se existe algum programa de criação suspeito

        producer = metadata.get("producer", "")

        creator = metadata.get("creator", "")


        suspicious_words = [

            "photoshop",

            "gimp",

            "canva"

        ]


        software = f"{producer} {creator}".lower()


        for word in suspicious_words:

            if word in software:

                evidences.append(

                    Evidence(

                        code="EDITING_SOFTWARE",

                        message=f"Documento criado ou editado usando {word}.",

                        severity="medium",

                        weight=20

                    )

                )


        return {

            "type": "PDF",

            "pages": len(pdf),

            "author": metadata.get("author"),

            "creator": creator,

            "producer": producer,

            "creation_date": metadata.get("creationDate"),

            "modification_date": metadata.get("modDate"),

            "encrypted": pdf.is_encrypted

        }, evidences




    def _analyze_image(self, file_path):


        image = Image.open(file_path)


        exif_data = {}


        exif = image.getexif()


        evidences = []


        for tag_id, value in exif.items():

            tag = ExifTags.TAGS.get(

                tag_id,

                tag_id

            )

            exif_data[tag] = value



        # Sem EXIF

        if not exif_data:


            evidences.append(

                Evidence(

                    code="NO_EXIF",

                    message="Imagem não possui metadados EXIF.",

                    severity="low",

                    weight=5

                )

            )



        return {

            "type": "IMAGE",

            "format": image.format,

            "width": image.width,

            "height": image.height,

            "mode": image.mode,

            "exif": exif_data

        }, evidences