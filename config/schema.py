"""
File used to define all schemas for graphql endpoint
"""
import graphene
from manifests.schema import Query as Manifest_Query

class Query(Manifest_Query, graphene.ObjectType):
    # Combine the queries from different apps
    pass

#not being used for now - FL 01/25/24
# class Mutation(graphene.ObjectType):
#     # Combine the mutations from different apps
#     pass


# schema = graphene.Schema(query=Query, mutation=Mutation)
schema = graphene.Schema(query=Query)