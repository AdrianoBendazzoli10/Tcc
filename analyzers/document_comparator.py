import re
import unicodedata


class DocumentComparator:

    def compare(self, documento1, documento2):

        campos1 = documento1.data.get("fields", {})
        campos2 = documento2.data.get("fields", {})

        nome1 = self._normalizar_nome(
            campos1.get("nome")
        )

        nome2 = self._normalizar_nome(
            campos2.get("nome")
        )

        cpf1 = self._normalizar_cpf(
            campos1.get("cpf")
        )

        cpf2 = self._normalizar_cpf(
            campos2.get("cpf")
        )

        datas1 = campos1.get("datas", [])
        datas2 = campos2.get("datas", [])

        resultado = {
            "nome": self._comparar(
                nome1,
                nome2
            ),

            "cpf": self._comparar(
                cpf1,
                cpf2
            ),

            "data": self._comparar_datas(
                datas1,
                datas2
            )
        }

        compatibilidade = self._calcular_compatibilidade(
            resultado
        )

        if compatibilidade is None:
            status = "SEM DADOS SUFICIENTES"

        elif compatibilidade >= 70:
            status = "COMPATIVEL"

        else:
            status = "INCONSISTENTE"

        return {
            "status": status,
            "campos": resultado,
            "compatibilidade": compatibilidade
        }

    # ---------- NOME ----------

    def _normalizar_nome(self, nome):

        if not nome:
            return None

        nome = unicodedata.normalize(
            "NFD",
            nome
        )

        nome = "".join(
            c
            for c in nome
            if unicodedata.category(c) != "Mn"
        )

        return " ".join(
            nome.upper().split()
        )

    # ---------- CPF ----------

    def _normalizar_cpf(self, cpf):

        if not cpf:
            return None

        cpf = re.sub(
            r"\D",
            "",
            cpf
        )

        return cpf if cpf else None

    # ---------- COMPARAÇÃO ----------

    def _comparar(self, valor1, valor2):

        # Se algum documento não possui
        # o campo, não podemos dizer que
        # os valores são diferentes.
        if not valor1 or not valor2:
            return "NAO_IDENTIFICADO"

        if valor1 == valor2:
            return "COMPATIVEL"

        return "DIVERGENTE"

    # ---------- DATAS ----------

    def _comparar_datas(self, datas1, datas2):

        if not datas1 or not datas2:
            return "NAO_IDENTIFICADO"

        datas1_normalizadas = {
            self._normalizar_data(data)
            for data in datas1
        }

        datas2_normalizadas = {
            self._normalizar_data(data)
            for data in datas2
        }

        if datas1_normalizadas & datas2_normalizadas:
            return "COMPATIVEL"

        return "DIVERGENTE"

    def _normalizar_data(self, data):

        if not data:
            return ""

        return data.replace(
            "-",
            "/"
        ).replace(
            " ",
            ""
        )

    # ---------- COMPATIBILIDADE ----------

    def _calcular_compatibilidade(self, resultados):

        pesos = {
            "nome": 40,
            "cpf": 50,
            "data": 10
        }

        pontos = 0
        peso_utilizado = 0

        for campo, resultado in resultados.items():

            # Campo não identificado não
            # deve ser tratado como divergência.
            if resultado == "NAO_IDENTIFICADO":
                continue

            peso = pesos[campo]

            peso_utilizado += peso

            if resultado == "COMPATIVEL":
                pontos += peso

        # Nenhum campo pôde ser comparado
        if peso_utilizado == 0:
            return None

        return round(
            (pontos / peso_utilizado) * 100,
            2
        )