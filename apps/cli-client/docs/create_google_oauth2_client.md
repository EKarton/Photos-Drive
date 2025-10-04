# Create your Google OAuth2 Client for Google Photos

## Description

This guide outlines how to create your Google OAuth2 client so that you can store your photos on Google Photos.

By the end of this guide, you will have created the OAuth2 client, and have obtained the client ID and client secrets so that the CLI can interact with the Google Photos and Google Drive APIs.

## Steps

1. Go to <https://cloud.google.com/cloud-console> and log into your Google account
2. Click on the "Console" button:

    ![image-1](./images/create_google_oauth2_client/image-1.png)

3. Click on the "Select Project" button and create a new project with any name:

    ![image-2](./images/create_google_oauth2_client/image-2.png)

    ![image-3](./images/create_google_oauth2_client/image-3.png)

    ![image-4](./images/create_google_oauth2_client/image-4.png)

4. Wait for your project to be created. Then select your project again:

    ![image-5](./images/create_google_oauth2_client/image-5.png)

    ![image-6](./images/create_google_oauth2_client/image-6.png)

5. Type in "Photos Library Api" in the search box, select "Photos Library Api", and click on "Enable":

    ![image-7](./images/create_google_oauth2_client/image-7.png)

    ![image-8](./images/create_google_oauth2_client/image-8.png)

    ![image-9](./images/create_google_oauth2_client/image-9.png)

6. Similarly, enable the Drive API by typing in "Drive API" in the search box, select "Drive API", and click on "Enable":

    ![image-10](./images/create_google_oauth2_client/image-10.png)

    ![image-11](./images/create_google_oauth2_client/image-11.png)

    ![image-12](./images/create_google_oauth2_client/image-12.png)

7. Create a new OAuth2 Consent Screen by going to to the APIs and Services tab, creating an External API, and fill in the details:

    ![image-13](./images/create_google_oauth2_client/image-13.png)

    ![image-14](./images/create_google_oauth2_client/image-14.png)

    ![image-15](./images/create_google_oauth2_client/image-15.png)

    ![image-16](./images/create_google_oauth2_client/image-16.png)

    ![image-17](./images/create_google_oauth2_client/image-17.png)

8. No special scopes is needed. So we can click on the `Save and Continue` button:

    ![image-18](./images/create_google_oauth2_client/image-18.png)

9. In the Test Users page, click on `Save and Continue`. We don't need to add test users since we will publish the app:

    ![image-19](./images/create_google_oauth2_client/image-19.png)

10. In the "Summary" page, scroll down and click on `Back to Dashboard` button:

    ![image-20](./images/create_google_oauth2_client/image-20.png)

11. In the main consent page, click on `Publish App`. A dialog will appear. Click on `Confirm`. It will publish the app:

    ![image-21](./images/create_google_oauth2_client/image-21.png)

12. Create the Client IDs and client secrets by going to the "Credentials" tab, clicking on "Create Credentials", select "OAuth Client ID", selecting "Web Application", and adding `http://localhost:8080/` in the authorized redirect uri:

    ![image-22](./images/create_google_oauth2_client/image-22.png)

    ![image-23](./images/create_google_oauth2_client/image-23.png)

    ![image-24](./images/create_google_oauth2_client/image-24.png)

    ![image-25](./images/create_google_oauth2_client/image-25.png)

    ![image-26](./images/create_google_oauth2_client/image-26.png)

    ![image-27](./images/create_google_oauth2_client/image-27.png)

13. Finally, click on the `Create` button. A dialog will appear with your Client ID and Client secrets. Download the file named as `client_secrets.json` and you now have your own client ID and client secrets:

    ![image-28](./images/create_google_oauth2_client/image-28.png)
