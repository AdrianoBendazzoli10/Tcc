import re
import unicodedata


class DocumentComparator:

    def compare(self, documento1, documento2):

        campos1 = documento1.data.get("fields", {})
        campos2 = documento2.data.get("fields", {})

        nome1 = self._normalizar_nome(campos1.get("nome"))
        nome2 = self._normalizar_nome(campos2.get("nome"))

        cpf1 = self._normalizar_cpf(campos1.get("cpf"))
        cpf2 = self._normalizar_cpf(campos2.get("cpf"))

        datas1 = campos1.get("datas", [])
        datas2 = campos2.get("datas", [])

        resultado = {
            "nome": self._comparar(nome1, nome2),
            "cpf": self._comparar(cpf1, cpf2),
            "data": self._comparar_datas(datas1, datas2)
        }

        compatibilidades = sum(resultado.values())

        if compatibilidades == 3:
            status = "COMPATIVEL"
        elif compatibilidades >= 2:
            status = "PROVAVELMENTE_COMPATIVEL"
        else:
            status = "INCONSISTENTE"

        return {
            "status": status,
            "campos": resultado
        }

    def _normalizar_nome(self, nome):

        if not nome:
            return ""

        nome = unicodedata.normalize("NFD", nome)
        nome = "".join(
            c for c in nome
            if unicodedata.category(c) != "Mn"
        )

        return " ".join(nome.upper().split())

    def _normalizar_cpf(self, cpf):

        if not cpf:
            return ""

        return re.sub(r"\D", "", cpf)

    def _comparar(self, valor1, valor2):

        if not valor1 or not valor2:
            return False

        return valor1 == valor2

    def _comparar_datas(self, datas1, datas2):

        if not datas1 or not datas2:
            return False

        return any(data in datas2 for data in datas1)
