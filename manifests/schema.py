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
        groupby_vars=graphene.List(graphene.String),
        host_app=graphene.String(required=True),
        host_model=graphene.String(required=True), 
        host_name_attr=graphene.String(required=True), 
        host_vars=graphene.List(graphene.String),
        description="Returns a JSON object that can be used to design Ansible inventory scripts for Dynamic Inventory\
            \n- groupby_app: The app the groupby model is apart of\
            \n- groupby_model: The model to group the host by (must be related to host)\
            \n- groupby_name_attr: The attribute to return as names for the group\
            \n- groupby_vars: The attributes to return as variables for groups\
            \n- host_app: The app the host model is apart of\
            \n- host_model: The model used for hosts\
            \n- host_name_attr: The attribute to return as host names\
            \n- host_vars: The attributes to return as variables for host"
    )

    def resolve_AnsibleInventory(self, info, groupby_app, groupby_model, groupby_name_attr, groupby_vars, host_app, host_model, host_name_attr, host_vars, **kwargs):

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

        # Validate if the inputs are valid field in models
        temp = groupby_vars + [groupby_name_attr]
        parent_model.objects.values_list(*temp)
        temp = host_vars + [host_name_attr]
        child_model.objects.values_list(*temp)

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
            values = {attr: list(parent_model.objects.filter(**{groupby_name_attr: item}).values_list(attr, flat=True))[0] for attr in groupby_vars}
            result[item] = {
                "hosts": hosts_bygroup,
                "vars": values,
            }
            all_hosts = all_hosts + hosts_bygroup

        result["_meta"] = {
            "hostvars": {
                host_name: {
                    attr: list(child_model.objects.filter(**{host_name_attr: host_name}).values_list(attr, flat=True))[0] for attr in host_vars
                } for host_name in all_hosts
            }
        }
        result["all"] = {
            "children": groups + ["ungrouped"]
        }

        return result