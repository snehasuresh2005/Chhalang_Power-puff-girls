1)Add you github token    (GITHUB_TOKEN = "github_token")
you can get your github token by following these steps:
    Log in to your GitHub account.
    Go to GitHub.com and sign in with your username and password.
    
    Navigate to your settings.
    Click your profile photo in the top-right corner of the page, then select Settings from the dropdown menu.
    
    Find the Developer Settings.
    On the left-hand sidebar, scroll down to the bottom and click Developer settings.
    
    Select Personal access tokens.
    In the left sidebar of the Developer settings, choose Personal access tokens, then click on Tokens (classic).
    
    Generate a new token.
    Click the Generate new token button. For most use cases, you'll want to select Generate new token (classic).
    
    Configure your token.
    
    Note: Give your token a descriptive name so you can remember what it's for (e.g., "CI/CD pipeline" or "local machine access").
    
    Expiration: Set an expiration date for the token. For security, it's best to set a limited time, such as 30 or 90 days.
    
    Scopes: This is the most crucial step. Scopes define the permissions of the token. You must select the necessary permissions for the tasks you plan to perform. For example, if you need to push code to repositories, you should check the repo scope. If you're using it for actions related to GitHub Actions, you might need the workflow scope. Choose the minimum required scopes to follow the principle of least privilege.
    
    Generate the token.
    After selecting the scopes, scroll to the bottom of the page and click Generate token.
    
    Copy the token.
    GitHub will display the newly generated token only once. Copy it immediately and store it in a secure location, like a password manager. You won't be able to see it again after you leave the page. If you lose it, you'll have to generate a new one.

    2) Add your github username (GITHUB_USERNAME = "username")
    3) Add a gemini api key  (GEMINI_API_KEY = "GOOGLE-API-KEY")
    you can get your gemini api key by following these steps
            Log in to Google AI Studio:
        Navigate to the Google AI Studio website. You'll need to sign in with your Google Account. If it's your first time, you'll be prompted to agree to the terms of service.
        
        
        Access the API Key section:
        Once you're in the AI Studio, look for the "Get API key" or "Get API key in Google AI Studio" button or link. It's usually located on the left-side navigation panel.
        
        
        Create your new key:
        Click on "Create API key" and then "Create API key in new project". This will instantly generate a new, unique API key for you.
        
        Copy and secure your key:
        After the key is generated, it will be displayed on the screen. It is crucial to copy this key immediately and store it in a secure location. Google AI Studio will only show you the key once. If you lose it, you will have to generate a new one.
