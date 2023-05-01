# import the necessary libraries
import json
import boto3
import logging
from src.custom_encoder.custom_encoder import CustomEncoder # an optional custom JSON encoder
from botocore.exceptions import ClientError # for handling client-side exceptions

# configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# specify the name of the DynamoDB table
dynamodbTableName = 'product-inventory'

# create a DynamoDB resource and then get a reference to the table
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(dynamodbTableName)

# specify the HTTP methods and paths for the API endpoints
getMethod = 'GET'
postMethod = 'POST'
patchMethod = 'PATCH'
deleteMethod = 'DELETE'
healthPath = '/health'
productPath = '/product'
productsPath = '/products'

# the main Lambda handler function
def handler(event, context):
    logger.info(event)
    # extract the HTTP method and path from the event
    httpMethod = event['httpMethod']
    path = event['path']
    # determine which endpoint was called and call the corresponding function
    if httpMethod == getMethod and path == healthPath:
        response = buildResponse(200)
    elif httpMethod == getMethod and path == productPath:
        response = getProduct(event['queryStringParameters']['productId'])
    elif httpMethod == postMethod and path == productPath:
        response = saveProduct(json.loads(event['body']))
    elif httpMethod == patchMethod and path == productPath:
        request_body = json.loads(event['body'])
        response = modifyProduct(request_body['productId'], request_body['updateKey'], request_body['updateValue'])
    elif httpMethod == deleteMethod and path == productPath:
        request_body = json.loads(event['body'])
        response = deleteProduct(request_body['productId'])
    elif httpMethod == getMethod and path == productsPath:
        response = getProducts()
    else:
        response = buildResponse(404, 'Not Found')
    # return the response to the caller
    return response

# function to get a product by its ID
def getProduct(productId):
    try:
        response = table.get_item(
            Key={
                'productId': productId
            }
        )
        if 'Item' in response:
            return buildResponse(200, response['Item'])
        else:
            return buildResponse(404, {'Message': 'Product %s not found ' % productId})
    except:
        logger.exception('Learn to handle this exception - getProduct()')

# function to get a list of all products
def getProducts():
    try:
        response = table.scan()
        result = response['Items']
        # if there are more items in the table, get them all and add them to the result
        while 'LastEvaluatedKey' in response:
            response = table.scan(LastEvaluatedKey=response['LastEvaluatedKey'])
            result.extend(response['Items'])
        # package the result in a dictionary and return it in the response
        body = {
            'products': result
        }
        return buildResponse(200, body)
    except ClientError as e:
        logger.exception('DynamoDB error in getProducts(): %s' % e.response['Error']['Message'])
        # Return an error response with a relevant status code and error message
        error_body = {
            'error': 'DynamoDB error',
            'message': e.response['Error']['Message']
        }
        return buildResponse(500, error_body) 
    
def saveProduct(requestBody):
    try:
        # Save the product in the DynamoDB table using the put_item method
        table.put_item(Item=requestBody)
        # Create a response body with the operation status, message and the saved item
        body = {
            'Operation': 'SAVE',
            'Message': 'SUCCESS',
            'Item': requestBody
        }
        # Return a 200 status code with the created response body
        return buildResponse(200, body)
    except ClientError as e:
        # Log the error message and return a 500 status code with the error message as the response body
        logger.exception('DynamoDB error in saveProduct(): %s' % e.response['Error']['Message'])
        error_body = {
            'error': 'DynamoDB error',
            'message': e.response['Error']['Message']
        }
        return buildResponse(500, error_body)
    except:
        # Log an exception in case of any other errors
        logger.exception('Unknown error in saveProduct()')
        error_body = {
            'error': 'Unknown error',
            'message': 'An unknown error occurred'
        }
        return buildResponse(500, error_body)
    
def modifyProduct(productId, updateKey, updateValue):
    try:
        # Update the item with the given productId using the update_item method
        response = table.update_item(
            Key={
                'productId': productId
            },
            UpdateExpression='SET %s = :value' %updateKey, # Update the attribute specified in updateKey with the given value
            ExpressionAttributeValues = {':value': updateValue},
            ReturnValues = 'UPDATED_NEW' # Return only the updated values
        )
        # Create a response body with the operation status, message and the updated attributes
        body = {
            'Operation': 'UPDATED',
            'Message': 'SUCCESS',
            'UpdatedAttributes': response
        }
        # Return a 200 status code with the created response body
        return buildResponse(200, body)
    except ClientError as e:
        # Log the error message and return a 500 status code with the error message as the response body
        logger.exception('DynamoDB error in modifyProduct(): %s' % e.response['Error']['Message'])
        error_body = {
            'error': 'DynamoDB error',
            'message': e.response['Error']['Message']
        }
        return buildResponse(500, error_body)
    except:
        # Log an exception in case of any other errors
        logger.exception('Unknown error in modifyProduct()')
        error_body = {
            'error': 'Unknown error',
            'message': 'An unknown error occurred'
        }
        return buildResponse(500, error_body)
         
def deleteProduct(productId):
    try:
        # Attempt to delete the item with the given productId using the delete_item method
        response = table.delete_item(
            Key = {
                'productId':productId
            },
            ReturnValues='ALL_OLD' # Return all the attributes of the deleted item
        )
        # Create a response body with the operation status, message and the deleted item
        body = {
            'Operation': 'DELETE',
            'Message': 'SUCCESS',
            'Item Deleted': response
        }
        # Return a 200 status code with the created response body
        return buildResponse(200, body)
    except:
        # Log an exception in case of errors
        logger.exception('An exception occurred while attempting to delete the product with ID %s' % productId)
    
def buildResponse(statusCode, body=None):
    # Create the basic response structure with the given status code and content type
    response = {
        "statusCode": statusCode,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        }
    }

    if body is not None:
        # Serialize the body as JSON using the custom encoder
        response['body'] = json.dumps(body, cls=CustomEncoder)
    return response


