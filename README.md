# WatchHouse


WatchHouse is an eCommerce platform for buying watches. The app is made eith the help of python django as backend tool and bootstrap with some css content for the frontend.

## About the Project

This project is built using the Django framework in Python. It allows users to browse and purchase watches with the following features:

- **Create an account** and manage user details
- **Login/Logout** functionality
- **Add products to the shopping cart**
- **Contact the admin** for support
- **Payment System**

## Database Structure

Due to database constraints, a CSV file has been used for the database in this project. Below is the structure of the database tables:

### `web_brand`
- `brand_id` (PK) - The primary key, identifying the brand
- `brand_name` - The name of the brand

### `web_type`
- `type_id` (PK) - The primary key, identifying the type of watch (e.g., digital, analog)
- `type_name` - The name of the watch type

### `web_gender`
- `gender_id` (PK) - The primary key, identifying the gender classification
- `gender_name` - The gender classification (e.g., Men's, Women's)

### `web_watch`
- `watch_id` (PK, Auto Increment) - The unique ID for each watch
- `title` - The title/name of the watch
- `brand_id` - Foreign key referencing the `web_brand` table
- `image_url` - URL of the image for the watch
- `price` - Price of the watch
- `gender_id` - Foreign key referencing the `web_gender` table
- `type_id` - Foreign key referencing the `web_type` table

### `web_user`
- `id` (PK, Auto Increment) - User ID
- `password` - User password
- `last_login` - Last login timestamp
- `is_superuser` - Boolean indicating if the user has admin privileges
- `username` - User's username
- `first_name` - User's first name
- `last_name` - User's last name
- `email` - User's email address
- `is_staff` - Boolean indicating if the user is a staff member
- `is_active` - Boolean indicating if the user account is active
- `date_joined` - Date the user account was created

