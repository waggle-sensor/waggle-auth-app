"""
File used to define schemas for manifest app that will be used in GraphQL endpoint
"""
import graphene
from graphql import GraphQLError
from django.apps import apps
from django.db import models
from graphene_django.types import DjangoObjectType
from .models import *

class Query(graphene.ObjectType):
    AnsibleInventory = graphene.Field( #TODO: implement behavior where groupby can be left out
        graphene.JSONString,
        groupby_app=graphene.String(required=True),
        groupby_model=graphene.String(required=True), 
        groupby_name_attr=graphene.String(required=True),
        host_app=graphene.String(required=True),
        host_model=graphene.String(required=True), 
        host_name_attr=graphene.String(required=True), 
        vars=graphene.List(graphene.String),
        description="Returns a JSON object that can be used to design Ansible inventory scripts for Dynamic Inventory\
            \n- groupby_app: The app the groupby model is apart of\
            \n- groupby_model: The model to group the host by (must be related to host)\
            \n- groupby_name_attr: The attribute to return as names for the group\
            \n- host_app: The app the host model is apart of\
            \n- host_model: The model used for hosts\
            \n- host_name_attr: The attribute to return as host names\
            \n- vars: The attributes to return as variables for groups and hosts"
    )

    def resolve_AnsibleInventory(self, info, groupby_app, groupby_model, groupby_name_attr, host_app, host_model, host_name_attr, vars, **kwargs):

        #try to get apps
        apps.get_app_config(groupby_app)
        apps.get_app_config(host_app)

        # Get the model class's dynamically
        parent_model = apps.get_model(app_label=groupby_app, model_name=groupby_model)
        child_model = apps.get_model(app_label=host_app, model_name=host_model)

        # Validate if ChildModel has a ForeignKey for ParentModel and get foreign key name
        foreign_key_name = None
        for field in child_model._meta.get_fields():
            if isinstance(field, models.ForeignKey) and field.related_model == parent_model:
                foreign_key_name = field.name
                break
        if not foreign_key_name:
            raise GraphQLError(f"{host_model} does not have a foreign key for {groupby_model}")

        # Validate if the name_attr(s) is a valid field in models
        parent_model.objects.values_list(groupby_name_attr, flat=True)
        child_model.objects.values_list(host_name_attr, flat=True)

        #split fields
        parent_fields = [field.name for field in parent_model._meta.fields]
        child_fields = [field.name for field in child_model._meta.fields]

        # Validate vars exist in parent_model or child_model
        all_fields = set(parent_fields) | set(child_fields)
        missing_fields = [x for x in vars if x not in all_fields]
        if missing_fields:
            raise GraphQLError(f"{', '.join(missing_fields)} field(s) do not exist in {groupby_model} and {host_model}")

        # split attr by model
        parent_vars = []
        child_vars = []
        for attr in vars:
            if attr in parent_fields:
                parent_vars.append(attr)
            if attr in child_fields:
                child_vars.append(attr)

        # Perform grouping based on the specified field
        groups_queryset = parent_model.objects.values_list(groupby_name_attr, flat=True).distinct()

        # Convert the QuerySet to a list
        groups = list(groups_queryset)
        result = {}
        all_hosts = []

        # configure result based on Ansible inventory scripts
        # NOTE: do I need to add ungrouped? - FL 01/25/2024
        for item in groups:                                                                
            hosts_bygroup = [host[host_name_attr] for host in child_model.objects.filter(**{f"{foreign_key_name}__{groupby_name_attr}": item}).values(host_name_attr)]
            values = {attr: list(parent_model.objects.filter(**{groupby_name_attr: item}).values_list(attr, flat=True))[0] for attr in parent_vars}
            result[item] = {
                "hosts": hosts_bygroup,
                "vars": values,
            }
            all_hosts = all_hosts + hosts_bygroup

        result["_meta"] = {
            "hostvars": {
                host_name: {
                    attr: child_model.objects.filter(**{host_name_attr: host_name}).values_list(attr, flat=True)[0] for attr in child_vars
                } for host_name in all_hosts
            }
        }
        result["all"] = {
            "children": groups + ["ungrouped"]
        }

        return result