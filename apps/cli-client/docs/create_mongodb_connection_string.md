# Creating your MongoDB connection string

## Description

This document outlines how to create your own connection string to your MongoDB database so that you can interact with your database via its APIs

## Steps

1. Go to <https://www.mongodb.com>, click on the login button, and log into your MongoDB account:

    ![Login 1](./images/creating-mongodb-connection-string/login-1.png)

    ![Login 2](./images/creating-mongodb-connection-string/login-2.png)

2. Once you're logged in, go to the `Database Access` tab, and click on the `Add new database user` button:

    ![DB access 1](./images/creating-mongodb-connection-string/db-access-1.png)

    ![DB access 2](./images/creating-mongodb-connection-string/db-access-2.png)

3. A new window appears. Set the authentication method to `Password`, specify the user's name, and click on auto-generate password:

    ![Create user 1](./images/creating-mongodb-connection-string/create-user-1.png)

    Copy the password to a notepad (it will be used later).

4. Scroll down, and set the built-in role to `Read and write to any database`, and then click on `Add user`:

    ![Create user 2](./images/creating-mongodb-connection-string/create-user-2.png)

    ![Create user 3](./images/creating-mongodb-connection-string/create-user-3.png)

5. It should show your new user in the users list with read and write permissions:

    ![Create user 4](./images/creating-mongodb-connection-string/create-user-4.png)

6. Now, click to the `Clusters` tab and click on the `Connect` button:

    ![Connect 1](./images/creating-mongodb-connection-string/connect-1.png)

7. Click on the `Drivers` button:

    ![Connect 2](./images/creating-mongodb-connection-string/connect-2.png)

8. Scroll down, and you will see a connection string template. Replace `<db_username>` and `<db_password>` with the name of the user you have made from step 3, and the user's password.

    ![Connect 3](./images/creating-mongodb-connection-string/connect-3.png)

9. All done! You have made your connection string for your new user.
