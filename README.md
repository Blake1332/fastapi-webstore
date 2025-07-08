```
# Clone the repository
git clone <repository-url>
cd fastapi-webstore

# Copy environment variables example and edit with your GitHub/GitLab OAuth credentials
cp env.example .env
#Make sure to create a goggle app password if you want to use email 2fa, its just like the gitlab one
#https://myaccount.google.com/apppasswords

# Make sure python3 and docker are installed! Start the application
docker-compose up -d
```
The application will be available at http://localhost:8091


# Web E-commerce Site
This is a E-commerce site that allows someone to use their browser to search and purchase products. The users will be able to do features like registration, shopping cart/checking out.  

User Registration and Login: Users can create accounts and log in. ✅<br>
Product Catalog: Display products with categories, descriptions, and prices.✅<br>
Search Functionality: Users can search for products by name or category.✅<br>
Basic Shopping Cart: Users can add and remove products from their cart.✅<br>
<table>
  <tr>
    <td><img src="/static/images/register.png" width="200"></td>
    <td><img src="/static/images/catalog.png" width="200"></td>
    <td><img src="/static/images/Search.png" width="200"></td>
    <td><img src="/static/images/clickaddtocart.png" width="200"></td>
    <td><img src="/static/images/cart.png" width="200"></td>
  </tr>
  <tr>
    <td>Registering a new user</td>
    <td>Veiw all products being sold</td>
    <td>Search for something</td>
    <td>Clicking add to cart</td>
    <td>Client side cart(Server side math)</td>
  </tr>
</table


Product Reviews and Ratings: Users can leave reviews and rate products.✅<br>
Wishlist: Users can save products to a wishlist for future purchase or to find later✅<br>
Intergration with g-mail and gitlab for 2fa for local users✅<br>
Allows uploads of images of products✅<br>
Error response using templates and some nice looking CSS✅<br>
Changes<br>
-Reworked CSS mostly for images to look nicer<br>
-New DB model, image updated below<br>
<table>
  <tr>
    <td><img src="/static/images/loggedin.png" width="200"></td>
    <td><img src="/static/images/2fa.png" width="200"></td>
    <td><img src="/static/images/productdetails.png" width="200"></td>
    <td><img src="/static/images/myproducts.png" width="200"></td>
    <td><img src="/static/images/addproduct.png" width="200"></td>
  </tr>
  <tr>
    <td>A logged in user using GitLab2FA</td>
    <td>2FA in my gmail</td>
    <td><p>Viewing a product details with a Review(as a different user)</p></td>
    <td>Products I am currently listing</td>
    <td>Create a product to sell</td>
  </tr>
</table>


# TODO - advanced back web info
Order History/Orders: Users can view their past orders and current order status. Items will have shipping dates based on quantity and size.📌<br>
Admin Panel: Administrators can manage products, categories, and user orders (1/2 done)📌<br>
Discounts and Promotions: Apply discounts and promotional codes during checkout.📌<br>
Checkout Process: Users can proceed to checkout, enter shipping details, and choose payment methods.(Maybe using a paypal I have made to test it?)📌<br>
TBD: Analytics Dashboard: View sales data and user activity reports. (Will be added in admin Panel)📌<br>

# Entities
Table users {
  user_id integer [primary key]
  username varchar
  password varchar
  email varchar
  address text
  phone varchar
  email_verification_code varchar
  email_verification_code_expires DateTime
  email_2fa_enabled Boolean
  first_name varchar
  last_name varchar
  shipping_address text
  billing_address text
  phone varchar
}

Table categories {
  category_id integer [primary key]
  name varchar
}

Table products {
  product_id integer [primary key]
  name varchar
  description text
  price integer
  category_id integer
  stock integer
}

Table orders {
  order_id integer [primary key]
  user_id integer
  order_date timestamp
  total_amount integer
  status varchar
}

Table order_items {
  order_item_id integer [primary key]
  order_id integer
  product_id integer
  quantity integer
  price integer
}

Table reviews {
  review_id integer [primary key]
  product_id integer
  user_id integer
  rating integer
  comment text
  date timestamp
}

Ref: users.user_id < orders.user_id

Ref: orders.order_id < order_items.order_id

Ref: order_items.product_id > products.product_id

Ref: products.category_id > categories.category_id

Ref: reviews.product_id > products.product_id

Ref: reviews.user_id > users.user_id
![image of schema](/static/images/schema.png)


# User Heirarchy
1. Administrator✅
2. User✅
3. Non-user✅

# Working Endpoints 
These endpoints will make the site work. Some will be only avaiable to Administrators.
## Users
1. POST /api/register - Register a new user.✅
2. POST /api/login - Authenticate a user.✅
3. GET /api/user/{id} - Get user details.✅

## Products
1. GET /api/products - List all products. ((non-user) maybe)✅
2. GET /api/products/{id} - Get details of a specific product. (non-user maybe)✅
3. POST /api/products - Add a new product (Logined user or admin).✅
4. PUT /api/products/{id} - Update a product (seller or admin).✅
5. DELETE /api/products/{id} - Delete a product (Admin only/ or seller)✅.<br>

## Cart
1. POST /api/cart - Add a product to the cart. (user) ✅.
2. GET /api/cart - View the cart. (user) ✅.
3. DELETE /api/cart/{id} - Remove a product from the cart.(user) ✅

## Reviews
1. POST /api/reviews - Add a review for a product. (user) ✅
2. GET /api/reviews/product/{productId} - Get all reviews for a product. (user) ✅
