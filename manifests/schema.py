"""
File used to define schemas for manifest app that will be used in GraphQL endpoint
"""
import graphene
#import django_filters
from django.apps import apps
from django.db import models
from graphene_django.types import DjangoObjectType
#from graphene_django.filter import DjangoFilterConnectionField
from .models import *

APP_NAME = "manifests"

# class HostFilter(django_filters.FilterSet):
#     class Meta:
#         model = Host
#         fields = ['name', 'group', 'var1', 'var2']

# class HostType(DjangoObjectType):
#     class Meta:
#         model = Host

class Query(graphene.ObjectType):
    group_hosts = graphene.Field( #TODO: are the vars required true?
        graphene.JSONString, 
        groupby_model=graphene.String(), 
        groupby_name_attr=graphene.String(), 
        host_model=graphene.String(), 
        host_name_attr=graphene.String(), 
        vars=graphene.List(graphene.String)
    )

    def resolve_group_hosts(self, info, groupby_model, groupby_name_attr, host_model, host_name_attr, vars, **kwargs):

        # Get the model class's dynamically
        try:
            parent_model = apps.get_model(app_label=APP_NAME, model_name=groupby_model)
        except LookupError:
            raise Exception(f"Invalid model name provided for groupby_model: {groupby_model} does not exist")
        try:
            child_model = apps.get_model(app_label=APP_NAME, model_name=host_model)
        except LookupError:
            raise Exception(f"Invalid model name provided for host_model: {host_model} does not exist")

        # Validate if ChildModel has a ForeignKey for ParentModel
        if not any(isinstance(field, models.ForeignKey) and field.related_model == parent_model for field in child_model._meta.get_fields()):
            raise Exception(f"{host_model} does not have a foreign key for {groupby_model}")

        # Validate if the name_attr(s) is a valid field in models
        parent_fields = [field.name for field in parent_model._meta.fields]
        if groupby_name_attr not in parent_fields:
            raise Exception(f"{groupby_name_attr} does not exist in {groupby_model}")

        child_fields = [field.name for field in child_model._meta.fields]
        if host_name_attr not in child_fields:
            raise Exception(f"{host_name_attr} does not exist in {host_model}")

        # Validate vars exist in parent_model or child_model
        all_fields = set(parent_fields) | set(child_fields)
        missing_fields = [x for x in vars if x not in all_fields]
        if missing_fields:
            raise Exception(f"{', '.join(missing_fields)} do not exist in {groupby_model} and {host_model}")

        # split attr by model
        parent_vars = []
        child_vars = []
        for attr in vars:
            if attr in parent_fields:
                parent_vars.append(attr)
            elif attr in child_fields:
                child_vars.append(attr)

        # Perform grouping based on the specified field
        groups = parent_model.objects.values(groupby_name_attr).distinct()
        result = {}
        all_hosts = []

        # configure result based on Ansible inventory scripts
        # NOTE: do I need to add ungrouped? - FL 01/25/2024
        for item in groups:
            hosts_bygroup = [host[host_name_attr] for host in child_model.objects.filter(**{f"{groupby_model}__{groupby_name_attr}": item[groupby_name_attr]}).values(host_name_attr)]
            values = {attr: list(parent_model.objects.filter(**{groupby_name_attr: item[groupby_name_attr]}).values_list(attr, flat=True)).first() for attr in parent_vars}
            result[item] = {
                "hosts": hosts_bygroup,
                "vars": values,
            }
            all_hosts.append(hosts_bygroup)

        result["_meta"] = {
            "hostvars": {
                host_name: {
                    attr: child_model.objects.filter(**{host_name_attr: host_name}).values_list(attr, flat=True).first() for attr in child_vars
                } for host_name in all_hosts
            }
        }
        result["all"] = {
            "children": groups + ["ungrouped"]
        }

        return result

schema = graphene.Schema(query=Query)