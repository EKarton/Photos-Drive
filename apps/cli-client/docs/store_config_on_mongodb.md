# Store Photos Drive Config on MongoDB

This document outlines how to set up your MongoDB account so that you can use your MongoDB account to store your Photos Drive config.

## Steps

1. Go to <https://www.mongodb.com>, click on the `Sign In` button, and log into your MongoDB account:

    ![Click on Sign In button](./images/store_config_on_mongodb/login_1.png)

    ![Enter credentials](./images/store_config_on_mongodb/login_2.png)

1. Once you're logged in, go to the `Database Access` tab:

    ![Click on Database Access tab](./images/store_config_on_mongodb/db_access_1.png)

1. Next, create a Read-Write user to your database, and save the username and password on your notepad:

    ![Click on Add New Database User button](./images/store_config_on_mongodb/create_db_user_1.png)

    ![Enter your username and autogenerate the password](./images/store_config_on_mongodb/create_db_user_2.png)

    ![Copy the password](./images/store_config_on_mongodb/create_db_user_3.png)

    ![Set DB access to read-write only](./images/store_config_on_mongodb/create_db_user_4.png)

    ![Click on Add User button](./images/store_config_on_mongodb/create_db_user_5.png)

1. Then, go to the Connections page:

    ![Click on Clusters > Connect](./images/store_config_on_mongodb/connect_1.png)

    ![Select Drivers as the way to connect to your config](./images/store_config_on_mongodb/connect_2.png)

1. Finally, obtain the connection string by filling in the username and password from your notepad:

    ![Obtain the connection string with username and password](./images/store_config_on_mongodb/connect_3.png)

1. That's all! That is how you can get your connection string to save your Photos Drive config on MongoDB.
