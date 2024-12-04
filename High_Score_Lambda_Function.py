import json
import boto3
import logging


s3_client = boto3.client('s3')
ses_client = boto3.client('ses')



def get_email_address(File):
  
  #Extracts the email address between <> from the File.
  
  parts = File.split("<")
  if len(parts) > 1:
    email = parts[1].split(">")[0]
    return email.strip()
  else:
    return None

def get_highest_score_classification(record):
    classes = record["Classes"]
    highest_class = max(classes, key=lambda x: x["Score"])
    return {
        "File": record["File"], 
        "TopClassification": highest_class["Name"], 
        "Score": highest_class["Score"]
        }
        
def send_notification_email(email, classification):
    sender_email = 'support@paxdivitiae.awsapps.com'
    
    if classification['TopClassification'] == 'MONEYTRANSFER':
        template_name = 'MONEYTRANSFER'
        template_data = {
            'Sub': classification['TopClassification'],
            'MTNID': 'MTNID8080',
            'STATUS': 'In Progress'
        }
    elif classification ['TopClassification'] == 'PROMOCODE':
        template_name = 'PROMOCODE'
        template_data = {
            'Sub': classification['TopClassification']
        }
    else:
        template_name = 'PASSRESET'
        template_data = {
            'Sub': 'Password Reset Request'
        }


    try:
        # Send the email using AWS SES
        ses_client = boto3.client('ses')
        response = ses_client.send_templated_email(
            Source=sender_email,
            Destination={
                'ToAddresses': [email]
            },
            Template=template_name,
            TemplateData=json.dumps(template_data)
        )

        # Check response for success
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print(f"Notification email sent successfully to {email}")
        else:
            # Handle unexpected HTTP status codes
            print(f"Failed to send email to {email}. HTTP Status Code: {response['ResponseMetadata']['HTTPStatusCode']}")
            print(f"Full Response: {json.dumps(response)}")
    except ses_client.exceptions.MessageRejected as e:
        # Handle message rejection errors
        print(f"Message rejected when sending email to {email}: {e}")
    except ses_client.exceptions.MailFromDomainNotVerifiedException as e:
        # Handle domain verification issues
        print(f"Mail FROM domain not verified for sending to {email}: {e}")
    except ses_client.exceptions.ConfigurationSetDoesNotExistException as e:
        # Handle missing configuration set
        print(f"Configuration set does not exist for email to {email}: {e}")
    except Exception as e:
        # Handle all other errors
        print(f"An error occurred while sending email to {email}: {e}")

 

def lambda_handler(event, context):
    
    
    results = []
 
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key_path = event['Records'][0]['s3']['object']['key']


    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=key_path)
        
        file_content = response['Body'].read().decode('utf-8').splitlines()

        for line in file_content:
            record = json.loads(line.strip())
            top_classification = get_highest_score_classification(record)
            email = get_email_address(record["File"])
            send_notification_email(email, top_classification)
            results.append({
                "classification":top_classification,
                "email":email})
            
       
    except Exception as e:
        # Log the error for debugging
        print(f"Error accessing or processing file: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

    # Return results
    return {
        'statusCode': 200,
        'body': json.dumps(results)
        
        
        
    }

   

      



