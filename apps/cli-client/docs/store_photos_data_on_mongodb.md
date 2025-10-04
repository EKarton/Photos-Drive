# Store Photos Metadata / Maps / Embeddings on MongoDB

This document outlines how to set up your MongoDB account so that you can use your MongoDB account to store your photo's metadata / maps data / embeddings.

## Steps

1. Go to <https://www.mongodb.com>, click on the `Sign In` button, and log into your MongoDB account:

    ![Click on Sign In button](./images/store_photos_data_on_mongodb/login_1.png)

    ![Enter credentials](./images/store_photos_data_on_mongodb/login_2.png)

1. Once you're logged in, go to the `Database Access` tab:

    ![Click on Database Access tab](./images/store_photos_data_on_mongodb/db_access_1.png)

1. Create an admin user for your database, and copy the username and password to your notepad:

    > Note: this is primary used for the CLI, where admin access is needed to know the total size of your database

    ![Click on Add New Database User button](./images/store_photos_data_on_mongodb/create_admin_user_1.png)

    ![Enter your username and autogenerate the password](./images/store_photos_data_on_mongodb/create_admin_user_2.png)

    ![Copy the password](./images/store_photos_data_on_mongodb/create_admin_user_3.png)

    ![Set DB access to admin only](./images/store_photos_data_on_mongodb/create_admin_user_4.png)

    ![Click on Add User button](./images/store_photos_data_on_mongodb/create_admin_user_5.png)

1. Create a read-only user for your database, and copy the username and password to your notepad:

    > Note: this is primary used for the web api, where the web api only has read-access to the database

    ![Click on Add New Database User button](./images/store_photos_data_on_mongodb/create_read_user_1.png)

    ![Enter your username and autogenerate the password](./images/store_photos_data_on_mongodb/create_read_user_2.png)

    ![Copy the password](./images/store_photos_data_on_mongodb/create_read_user_3.png)

    ![Set DB access to read only](./images/store_photos_data_on_mongodb/create_read_user_4.png)

    ![Click on Add User button](./images/store_photos_data_on_mongodb/create_read_user_5.png)

1. Then, go to the Connections page:

    ![Click on Clusters > Connect](./images/store_photos_data_on_mongodb/connect_1.png)

    ![Select Drivers as the way to connect to your config](./images/store_photos_data_on_mongodb/connect_2.png)

1. Next, obtain the connection string of your admin user by filling in the username and password of your admin user saved on your notepad:

    ![Obtain the admin connection string with username and password](./images/store_photos_data_on_mongodb/connect_3.png)

1. Finally, obtain the connection string of your read-only user by repeating the previous step but with the username and password of your read-only user saved on your notepad.

1. That's all! That is how you can get the admin and read-only connection strings of your database to store your photos data on MongoDB.
