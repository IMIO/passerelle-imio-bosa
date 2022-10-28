import requests
from django.db import models
from django.http import HttpResponse
from django.urls import reverse
from django.core.exceptions import ValidationError
from passerelle.base.models import BaseResource
from passerelle.utils.api import endpoint
from passerelle.utils.jsonresponse import APIError
from requests import RequestException


def validate_url(value):
    if value.endswith("/"):
        raise ValidationError(
            '%(value)s ne dois pas finir avec un "/"',
            params={'value': value},
        )


class ApimsBaecConnector(BaseResource):
    """
    Connecteur APIMS BAEC

    Attributes
    ----------
    url : str
        url used to connect to APIMS BAEC
    username : str
        username used to connect to APIMS BAEC
    password : str
        password used to connect to APIMS BAEC
    municipality_token : str
        token used to identify municipality to APIMS BAEC

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
        default="https://api-staging.imio.be/bosa/v1"
    )
    username = models.CharField(
        max_length=128,
        blank=True,
        help_text="Utilisateur APIMS BAEC",
        verbose_name="Utilisateur",
    )
    password = models.CharField(
        max_length=128,
        blank=True,
        help_text="Mot de passe APIMS BAEC",
        verbose_name="Mot de passe",
    )
    municipality_token = models.CharField(
        max_length=128,
        blank=True,
        help_text="Token d'identification de l'organisme dans APIMS BAEC",
        verbose_name="Token d'identification",
    )
    api_description = "Connecteur permettant d'intéragir avec APIMS BAEC"
    category = "Connecteurs iMio"

    class Meta:
        verbose_name = "Connecteur APIMS BAEC"

    @property
    def session(self):
        session = requests.Session()
        session.auth = (self.username, self.password)
        session.headers.update({
            "Accept": "application/json",
            "X-IMIO-MUNICIPALITY-TOKEN": self.municipality_token
        })
        return session

    @endpoint(
        name="test",
        perm="can_access",
        description="Test Connexion",
        long_description="Valider la connexion entre APIMS et Publik",
        serializer_type="json-api",
        display_order=0,
        display_category="Test"
    )
    def test(self, request):
        url = f"{self.url}/test"
        self.logger.info("Lancement d'un test")
        return self.session.get(url).json()

    @endpoint(
        name="list-person-documents",
        perm="can_access",
        description="Lister les documents",
        long_description="Liste les documents disponibles pour une personne identifiée par son numéro de registre national",
        parameters={
            "rn": {
                "description": "Numéro de Registre national",
                "example_value": "89041522261",
            },
            "category": {
                "description": "Catégorie du document",
                "example_value": "BIRTH_CERTIFICATE",
            }
        },
        serializer_type="json-api",
        display_order=0,
        display_category="Documents",
    )
    def list_person_documents(self, request, rn, category=None):
        """ Gets available documents for the person
        Parameters
        ----------
        rn : str
            National Registration number of the person
        category : str
            Category of the document
        Returns
        -------
        dict
            all document with reference and available type
        """
        url = f"{self.url}/civil-status-documents/{rn}"

        self.logger.info("Liste des documents disponibles")
        try:
            response = self.session.get(url, params={"category": category})
        except RequestException as e:
            self.logger.warning(f'BAEC APIMS Error: {e}')
            raise APIError(f'BAEC APIMS Error: {e}')

        json_response = None
        try:
            json_response = response.json()
        except ValueError:
            self.logger.warning('BAEC APIMS Error: bad JSON response')
            raise APIError('BAEC APIMS Error: bad JSON response')

        try:
            response.raise_for_status()
        except RequestException as e:
            self.logger.warning(f'BAEC APIMS Error: {e} {json_response}')
            raise APIError(f'BAEC APIMS Error: {e} {json_response}')
        return json_response

    @endpoint(
        name="read-document",
        perm="can_access",
        methods=["post"],
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
        display_order=1,
        display_category="Documents"
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

        url = f"{self.url}/civil-status-documents/{rn}/{certificate_reference}/{certificate_type}"

        self.logger.info("Récupération du document PDF")
        try:
            response = requests.get(url, auth=(self.username, self.password), headers={
                "X-IMIO-MUNICIPALITY-TOKEN": self.municipality_token
            })
        except Exception as e:
            self.logger.warning(f'BAEC APIMS Error: {e}')
            raise APIError(f'BAEC APIMS Error: {e}')

        pdf_response = None
        try:
            pdf_response = HttpResponse(response.content, content_type="application/pdf")
        except ValueError:
            self.logger.warning('BAEC APIMS Error: bad PDF response')
            raise APIError('BAEC APIMS Error: bad PDF response')

        try:
            response.raise_for_status()
        except Exception as e:
            self.logger.warning(f'BAEC APIMS Error: {e}')
            raise APIError(f'BAEC APIMS Error: {e}')
        return pdf_response

    @endpoint(
        name="request-document-migration",
        perm="can_access",
        methods=["post"],
        description="Demander l'importation d'un acte dans la BAEC",
        parameters={
            "migration_command": {
                "description": "Numéro d'identifiant pour la demande de migration",
                "example_value": "06715166470089041522261F1504198901111202115041989Li",
            },
        },
        display_category="Documents"
    )
    def request_document_migration(self, request, migration_command):
        """ Post request to migrate a document to the BAEC
        migration_command : str
            ID to migrate request document
        """
        url = f"{self.url}/civil-status-documents/migration-requests"

        json_data = {'migration_command': migration_command}

        self.logger.info("Envoi d'une demande de migation dans la BAEC")

        try:
            response = self.session.post(url, json=json_data)
        except RequestException as e:
            self.logger.warning(f'BAEC APIMS Error: {e}')
            raise APIError(f'BAEC APIMS Error: {e}')

        json_response = None
        try:
            json_response = response.json()
        except ValueError:
            self.logger.warning('BAEC APIMS Error: bad JSON response')
            raise APIError('BAEC APIMS Error: bad JSON response')

        try:
            response.raise_for_status()
        except RequestException as e:
            self.logger.warning(f'BAEC APIMS Error: {e} {json_response}')
            raise APIError(f'BAEC APIMS Error: {e} {json_response}')
        return json_response
