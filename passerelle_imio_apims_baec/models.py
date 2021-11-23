from builtins import str

import requests
from django.db import models
from django.http import Http404
from django.http import HttpResponse
from django.urls import reverse
from passerelle.base.models import BaseResource
from passerelle.compat import json_loads
from passerelle.utils.api import endpoint
from passerelle.utils.jsonresponse import APIError
from requests.exceptions import ConnectionError


class ApimsBaecConnector(BaseResource):
    """
    Connecteur APIMS BAEC
    """
    url = models.CharField(
        max_length=128,
        blank=True,
        verbose_name="URL",
        help_text="URL de APIMS BAEC",
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
        name="Tester la connexion",
        perm="can_access",
        description="Valider la connexion entre APIMS et Publik",
    )
    def test(self, request):
        url = self.url  # Url et endpoint à contacter
        return self.session.get(url).json()

    @endpoint(
        name="Lister des documents d'une personne",
        perm="can_access",
        description="Liste les documents disponibles pour une personne identifiée par son numéro de registre national"
    )
    def read_person_documents(self, request):
        url = f"{self.url}/{request.GET.person_nrn}"
        return self.session.get(url).json()

    @endpoint(
        name="Lire le document d'une personne",
        perm="can_access",
        description="Lire le document d'une personne"
    )
    def read_document(self, request):
        url = f"{self.url}/{request.GET.person_nrn}/{request.GET.certificate_reference}/{request.GET.certificate_type}"
        return self.session.get(url).json()