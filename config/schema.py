"""
File used to define all schemas for graphql endpoint
"""
import graphene
import manifests.schema

class Query(manifests.schema.Query):
    """Root for converge Graphql queries"""
    # Combine the queries from different apps
    pass

#not being used for now - FL 01/25/24
# class Mutation(graphene.ObjectType):
#     # Combine the mutations from different apps
#     pass


# schema = graphene.Schema(query=Query, mutation=Mutation)
schema = graphene.Schema(query=Query,auto_camelcase=False)