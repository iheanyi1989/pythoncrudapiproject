import jwt  # Import the JWT library
import os

def handler(event, context):
    
    token = event['authorizationToken'].split(' ')[-1]  # Extract the JWT token from the event object
    jwt_secret = os.environ['JWT_SECRET'] # Make an object of the secret
    resource = event['methodArn']  # Extract the method ARN from the event object
    
    print("Event:", event)  # Print the event object for debugging
    print("Token:", token)  # Print the extracted token for debugging
    print("MethodArn", resource)  # Print the resource ARN for debugging
    
    try:
        auth = "Deny"  # Set default authorization to 'Deny'
        decoded_token = jwt.decode(token, 'test123', algorithms=['HS256'])  # Decode the JWT token using the secret key
        print("Decoded_token:", decoded_token)  # Print the decoded token for debugging
        principal_id = decoded_token.get('sub')  # Extract the principal ID from the decoded token
        
        if principal_id:
            auth = "Allow"  # If the principal ID exists, set authorization to 'Allow'
        return generate_policy(principal_id, auth)  # Generate and return the IAM policy
    
    except jwt.InvalidTokenError:
        raise Exception('Invalid token')  # If the token is invalid, raise an exception


def generate_policy(principal_Id, auth):
    principalId = principal_Id  # Set the principal ID
    policy = {  # Create the IAM policy
                'Version': '2012-10-17',
                'Statement': [
                    {
                        'Action': 'execute-api:Invoke',
                        'Effect': auth,  # Set the effect to the value of the 'auth' variable ('Allow' or 'Deny')
                        'Resource': 'arn:aws:execute-api:us-east-1:384206995652:*' # Set the resource to the method ARN extracted from the event object
                    }
                ]
            }
    return {
        'principalId': principalId,  # Include the principal ID in the response
        'policyDocument': policy  # Include the generated IAM policy in the response
    }
