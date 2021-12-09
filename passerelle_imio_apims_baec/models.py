import requests
from django.db import models
from django.http import HttpResponse
from django.urls import reverse
from django.core.exceptions import ValidationError
from passerelle.base.models import BaseResource
from passerelle.utils.api import endpoint
from passerelle.utils.jsonresponse import APIError

def validate_url(value):
    if value.endswith("/"):
        raise ValidationError(
            ('%(value)s ne dois pas finir avec un "/"'),
            params={'value': value},
        )
class ApimsBaecConnector(BaseResource):
    """
    Connecteur APIMS BAEC

    Attributes
    ----------
    url : str
        a formatted string to print out what the animal says
    username : str
        username used to connect to apims
    password : str
        password used to connect to apims

    Methods
    -------
    list_person_documents(rn)
        Gets available documents for the person
    read_document (rn, certificate_reference, certificate_type)
       Get asked document as PDF
    """
    url = models.URLField(
        max_length=128,
        blank=True,
        verbose_name="URL",
        help_text="URL de APIMS BAEC",
        validators=[validate_url],
        default="https://api-staging.imio.be/bosa/v1/civil-status-documents"
    )
    username = models.CharField(
        max_length=128,
        blank=True,
        verbose_name="Utilisateur",
    )
    password = models.CharField(
        max_length=128,
        blank=True,
        verbose_name="Mot de passe",
    )
    api_description = "Connecteur permettant d'intéragir avec APIMS BAEC"
    category = "Connecteurs iMio"

    class Meta:
        verbose_name = "Connecteur APIMS BAEC"

    @property
    def session(self):
        session = requests.Session()
        session.auth = (self.username, self.password)
        session.headers.update({"Accept": "application/json"})
        return session

    @endpoint(
        name="test",
        perm="can_access",
        description="Valider la connexion entre APIMS et Publik",
        serializer_type="json-api",
    )
    def test(self, request):
        url = self.url
        return self.session.get(url).json()

    @endpoint(
        name="list-person-documents",
        perm="can_access",
        description="Liste les documents disponibles pour une personne identifiée par son numéro de registre national",
        parameters={
            "rn": {
                "description": "Numéro de Registre national",
                "example_value": "89041522261",
            },
        },
        serializer_type="json-api",
    )
    def list_person_documents(self, request, rn):
        """ Gets available documents for the person
        Parameters
        ----------
        rn : str
            National Registration number of the person
        Returns
        -------
        dict
            all document with reference and available type
        """
        url = f"{self.url}/{rn}"
        return self.session.get(url).json()


    @endpoint(
        name="read-document",
        perm="can_access",
        description="Lire le document d'une personne",
        parameters={
            "rn": {
                "description": "Numéro de Registre national",
                "example_value": "00000000097",
            },
            "certificate_reference": {
                "description": "Référence du document",
                "example_value": "20190000467415",
            },

            "certificate_type": {
                "description": "Type de document",
                "example_value": "E",
            },
        },
    )
    def read_document(self, request, rn, certificate_reference, certificate_type):
        """ Get asked document as PDF
        Parameters
        ----------
        rn : str
            National Registration number of the person
        certificate_reference : str
            Reference of the certificate
        certificate_type : str
            Type of document
        Returns
        -------
        PDF document
        """
        url = f"{self.url}/{rn}/{certificate_reference}/{certificate_type}"
        response = requests.get(url, auth=(self.username, self.password))
        if response.status_code >= 400:
           raise APIError("502 Bad gateway", http_status=502, data={"target_url": url, "error": response.status_code})
        return HttpResponse(response.content, content_type="application/pdf")
