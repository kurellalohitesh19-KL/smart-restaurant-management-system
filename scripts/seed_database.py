"""
Idempotent Database Seed Script
Smart Restaurant Management System

Safely seeds operational records for all restaurants:
- Tables across diverse capacities
- Menu categories & menu items
- Staff assignments
- Sample reservations & orders

Rules:
- 100% IDEMPOTENT: Checks for existence before inserting.
- NEVER deletes or overwrites existing data.
- NEVER inserts fake/mock records during regular Flask startup.
- Designed to be run explicitly: python scripts/seed_database.py
"""

import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import io
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from decimal import Decimal
from datetime import datetime, date, time, timedelta, timezone
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant, RestaurantStaff, CustomerRestaurant
from app.models.table import Table
from app.models.menu import MenuCategory, MenuItem
from app.models.reservation import Reservation
from app.models.order import Order, OrderItem

def seed_database():
    app = create_app('development')
    
    with app.app_context():
        print("Starting idempotent database seeding for MySQL (smart_restaurant_db)...")
        
        # 1. Verify / Seed Super Admin
        admin = User.query.filter_by(email='admin@test.com').first()
        if not admin:
            admin = User(name='Super Admin', email='admin@test.com', role='super_admin', is_active=True)
            admin.set_password('Admin@123')
            db.session.add(admin)
            print("  [+] Created Super Admin: admin@test.com")
        else:
            print("  [=] Super Admin already exists.")
            
        # 2. Verify / Seed Demo Customers
        demo_customers = [
            ('Anand Kumar', 'anand.customer@example.com', '9876543210'),
            ('Sneha Patel', 'sneha.customer@example.com', '9876543211'),
            ('Rajesh V', 'rajesh.customer@example.com', '9876543212')
        ]
        customers = []
        for name, email, phone in demo_customers:
            cust = User.query.filter_by(email=email).first()
            if not cust:
                cust = User(name=name, email=email, phone=phone, role='customer', is_active=True)
                cust.set_password('Customer@123')
                db.session.add(cust)
                print(f"  [+] Created Customer: {email}")
            customers.append(cust)
        db.session.commit()
        
        # 3. Ensure All 5 Restaurants Have Owners & Details
        # Restaurant definitions with authentic Trichy addresses
        rest_defs = [
            {
                'id': 1,
                'name': 'Spice Garden',
                'owner_email': 'arun.owner.demo@example.com',
                'owner_name': 'Arun Kumar',
                'city': 'Tiruchirappalli',
                'address': 'SRM Nagar, near SRM Institute of Science and Technology, Kattankulathur / Trichy',
                'description': 'Authentic traditional South and North Indian delicacies prepared with aromatic hand-ground spices and fresh local produce.'
            },
            {
                'id': 2,
                'name': 'Golden Millet Kitchen',
                'owner_email': 'priya.owner.demo@example.com',
                'owner_name': 'Priya Sharma',
                'city': 'Tiruchirappalli',
                'address': 'No. 14, Salai Road, Thillai Nagar, Tiruchirappalli',
                'description': 'Wholesome organic dining focusing on ancient Indian millets, farm-fresh ingredients, and nourishing traditional recipes.'
            },
            {
                'id': 3,
                'name': 'Urban Crave Bistro',
                'owner_email': 'karthik.owner.demo@example.com',
                'owner_name': 'Karthik Raj',
                'city': 'Tiruchirappalli',
                'address': '22, Williams Road, Cantonment, Tiruchirappalli',
                'description': 'Contemporary continental dining featuring artisan wood-fired pizzas, gourmet pastas, sizzlers, and specialty mocktails.'
            },
            {
                'id': 4,
                'name': 'Royal Pepper House',
                'owner_email': 'divya.owner.demo@example.com',
                'owner_name': 'Divya Lakshmi',
                'city': 'Tiruchirappalli',
                'address': '45, Rockins Road, Cantonment, Tiruchirappalli',
                'description': 'Fiery Chettinad and Kongu Nadu regional specialties bursting with black pepper, dry red chillies, and coastal coastal flair.'
            },
            {
                'id': 5,
                'name': 'Moonlight Café & Desserts',
                'owner_email': 'naveen.owner.demo@example.com',
                'owner_name': 'Naveen Kumar',
                'city': 'Tiruchirappalli',
                'address': '8, Sastri Road, Thillai Nagar, Tiruchirappalli',
                'description': 'Chic dessert lounge and artisan coffee bar serving handcrafted pastries, Belgium waffles, and European espresso roasts.'
            }
        ]
        
        for rdef in rest_defs:
            owner = User.query.filter_by(email=rdef['owner_email']).first()
            if not owner:
                owner = User(name=rdef['owner_name'], email=rdef['owner_email'], role='restaurant_owner', is_active=True)
                owner.set_password('Owner@123')
                db.session.add(owner)
                db.session.commit()
                print(f"  [+] Created Owner: {rdef['owner_email']}")
                
            restaurant = Restaurant.query.filter_by(name=rdef['name']).first()
            if not restaurant:
                restaurant = Restaurant(
                    name=rdef['name'],
                    owner_id=owner.id,
                    address=rdef['address'],
                    city=rdef['city'],
                    state='Tamil Nadu',
                    description=rdef['description'],
                    is_active=True
                )
                db.session.add(restaurant)
                db.session.commit()
                print(f"  [+] Created Restaurant: {rdef['name']}")
            else:
                # Update address/description if empty
                if not restaurant.address or not restaurant.description:
                    restaurant.address = rdef['address']
                    restaurant.description = rdef['description']
                    db.session.commit()
                    print(f"  [*] Updated metadata for: {rdef['name']}")
                    
        # 4. Seed Dining Tables for Restaurants 2 through 5
        standard_tables = [
            ('T1', 2), ('T2', 2), ('T3', 4), ('T4', 4),
            ('T5', 4), ('T6', 6), ('T7', 6), ('T8', 8), ('T9', 10)
        ]
        
        for rest in Restaurant.query.filter_by(is_active=True).all():
            existing_tables = Table.query.filter_by(restaurant_id=rest.id).count()
            if existing_tables == 0:
                for t_num, cap in standard_tables:
                    t = Table(restaurant_id=rest.id, table_number=t_num, capacity=cap, status='available')
                    db.session.add(t)
                print(f"  [+] Added {len(standard_tables)} tables for restaurant #{rest.id} ({rest.name})")
        db.session.commit()
        
        # 5. Seed Staff Members for Restaurants 2 through 5
        staff_defs = [
            (2, 'Kavitha Staff', 'kavitha.staff@example.com', 'Floor Supervisor'),
            (3, 'Manoj Staff', 'manoj.staff@example.com', 'Sous Chef'),
            (4, 'Deepak Staff', 'deepak.staff@example.com', 'Captain Waiter'),
            (5, 'Swathi Staff', 'swathi.staff@example.com', 'Barista')
        ]
        
        for rest_id, s_name, s_email, s_desig in staff_defs:
            rest = Restaurant.query.get(rest_id)
            if not rest:
                continue
            s_user = User.query.filter_by(email=s_email).first()
            if not s_user:
                s_user = User(name=s_name, email=s_email, role='restaurant_staff', is_active=True)
                s_user.set_password('Staff@123')
                db.session.add(s_user)
                db.session.commit()
            
            s_rec = RestaurantStaff.query.filter_by(user_id=s_user.id, restaurant_id=rest.id).first()
            if not s_rec:
                s_rec = RestaurantStaff(user_id=s_user.id, restaurant_id=rest.id, designation=s_desig)
                db.session.add(s_rec)
                print(f"  [+] Assigned staff {s_email} to restaurant #{rest.id} ({rest.name})")
        db.session.commit()

        # 6. Seed Categorized Menus for Restaurants 2 through 5
        restaurant_menus = {
            'Golden Millet Kitchen': {
                'Millet Breakfast': [
                    ('Kodo Millet Idli', 'Steamed kodo millet cakes served with three house chutneys and sambar', 70.00),
                    ('Foxtail Millet Dosa', 'Crisp crepe made of foxtail millet and lentils with coconut chutney', 95.00),
                    ('Barnyard Millet Upma', 'Wholesome breakfast tempered with mustard, curry leaves, and roasted cashews', 85.00),
                    ('Ragi Sevai', 'Steamed finger millet string hoppers seasoned with fresh grated coconut', 80.00),
                ],
                'Organic Lunch Thali': [
                    ('Royal Millet Meal', 'Complete balanced platter of millet rice, sambar, rasam, kootu, poriyal, curd & appalam', 210.00),
                    ('Little Millet Bisi Bele Bath', 'Rich spicy lentil millet rice cooked with vegetables and pure ghee', 160.00),
                    ('Proso Millet Curd Rice', 'Probiotic millet curd rice tempered with pomegranate, ginger, and green chilli', 120.00),
                ],
                'Healthy Herbal Coolers': [
                    ('Nannari Sarbath', 'Traditional wild sarsaparilla root cooler with fresh lime', 60.00),
                    ('Ragi Malt Cooler', 'Chilled sprouted finger millet beverage infused with cardamom and jaggery', 75.00),
                    ('Sukku Coffee', 'Herbal dry ginger and coriander decoction sweetened with palm jaggery', 45.00),
                ]
            },
            'Urban Crave Bistro': {
                'Wood-Fired Pizza': [
                    ('Margherita Classica', 'San Marzano tomato sauce, fresh buffalo mozzarella, and sweet basil', 320.00),
                    ('Smoked Cottage Cheese Pizza', 'Charred paneer cubes, bell peppers, red onions, and mozzarella', 360.00),
                    ('BBQ Chicken Supreme', 'Tender shredded chicken, tangy smoked barbecue sauce, and cheddar', 420.00),
                ],
                'Gourmet Pastas & Mains': [
                    ('Creamy Truffle Penne', 'Penne tossed in garlic parmesan white sauce with wild mushrooms', 340.00),
                    ('Spicy Arrabbiata', 'Classic rigatoni in fiery red chilli tomato reduction with fresh herbs', 290.00),
                    ('Grilled Paneer Steak Sizzler', 'Herbed paneer steak served with butter rice, sautéed greens, and pepper sauce', 380.00),
                ],
                'Specialty Beverages': [
                    ('Peach & Basil Iced Tea', 'Brewed black tea with peach puree and hand-torn basil', 130.00),
                    ('Classic Cold Brew', 'Steeped dark roast Arabica coffee served over crystal ice', 150.00),
                    ('Passion Fruit Sparkler', 'Zesty passion fruit pulp with sparkling lime soda', 140.00),
                ]
            },
            'Royal Pepper House': {
                'Chettinad Starters': [
                    ('Pepper Chicken Fry', 'Succulent chicken morsels roasted with freshly crushed black peppercorns', 280.00),
                    ('Chettinad Mushroom Chukka', 'Button mushrooms tossed in fiery ground shallot and fennel masala', 210.00),
                    ('Vazhaipoo Vadai', 'Crispy spiced banana flower fritters served with mint relish', 120.00),
                ],
                'Signature Curries': [
                    ('Chettinad Kozhi Curry', 'Traditional country chicken cooked in 18 hand-ground spice gravy', 320.00),
                    ('Ennai Kathirikai Kulambu', 'Baby brinjals simmered in tangy sesame oil and tamarind gravy', 220.00),
                    ('Pepper Mutton Chukka', 'Tender lamb chunks dry roasted with black pepper and curry leaves', 390.00),
                ],
                'Breads & Rice': [
                    ('Ceylon Egg Parotta', 'Layered flaky parotta stuffed with spiced eggs and onions', 130.00),
                    ('Bun Parotta (2 pcs)', 'Fluffy deep-fried Madurai-style bun parottas served with salna', 90.00),
                    ('Seeraga Samba Chicken Biryani', 'Fragrant short-grain rice cooked with succulent chicken and aromatic herbs', 290.00),
                ]
            },
            'Moonlight Café & Desserts': {
                'Artisan Desserts': [
                    ('Classic Belgian Chocolate Waffle', 'Warm crisp waffle smothered with melted dark Belgian chocolate', 190.00),
                    ('New York Cheesecake', 'Velvety baked cream cheese slice on a crunchy butter graham crust', 240.00),
                    ('Tiramisu Italiano', 'Espresso-soaked ladyfingers layered with rich mascarpone zabaglione', 220.00),
                    ('Red Velvet Cupcake', 'Soft cocoa sponge with whipped Madagascar vanilla cream cheese frosting', 90.00),
                ],
                'Gourmet Coffee & Tea': [
                    ('Hazelnut Cappuccino', 'Double espresso shot with steamed velvety milk and roasted hazelnut', 160.00),
                    ('Caramel Macchiato', 'Steamed milk stained with espresso and finished with butter caramel drizzle', 170.00),
                    ('Cafe Mocha', 'Espresso blended with premium Dutch cocoa and silky steamed milk', 180.00),
                    ('Matcha Green Tea Latte', 'Ceremonial grade Japanese Uji matcha whisked with fresh almond milk', 210.00),
                ]
            }
        }
        
        for r_name, cat_dict in restaurant_menus.items():
            rest = Restaurant.query.filter_by(name=r_name).first()
            if not rest:
                continue
                
            for cat_name, items_list in cat_dict.items():
                category = MenuCategory.query.filter_by(restaurant_id=rest.id, name=cat_name).first()
                if not category:
                    category = MenuCategory(restaurant_id=rest.id, name=cat_name, is_active=True)
                    db.session.add(category)
                    db.session.commit()
                    print(f"  [+] Created Category '{cat_name}' for {r_name}")
                    
                for i_name, i_desc, i_price in items_list:
                    item = MenuItem.query.filter_by(restaurant_id=rest.id, name=i_name).first()
                    if not item:
                        item = MenuItem(
                            restaurant_id=rest.id,
                            category_id=category.id,
                            name=i_name,
                            description=i_desc,
                            price=Decimal(str(i_price)),
                            is_available=True
                        )
                        db.session.add(item)
            db.session.commit()
            print(f"  [+] Verified / seeded all menu items for: {r_name}")
            
        # 7. Seed Sample Reservations Across Restaurants
        active_cust = customers[0] if customers else User.query.filter_by(role='customer').first()
        if active_cust:
            for rest in Restaurant.query.filter_by(is_active=True).all():
                table = Table.query.filter_by(restaurant_id=rest.id, status='available').first()
                if table:
                    # Check if reservation already exists
                    has_res = Reservation.query.filter_by(restaurant_id=rest.id, customer_id=active_cust.id).first()
                    if not has_res:
                        tomorrow = datetime.now().date() + timedelta(days=1)
                        res = Reservation(
                            customer_id=active_cust.id,
                            restaurant_id=rest.id,
                            table_id=table.id,
                            reservation_date=tomorrow,
                            start_time=time(19, 0),
                            end_time=time(20, 0),
                            number_of_guests=min(2, table.capacity),
                            status='confirmed'
                        )
                        db.session.add(res)
                        print(f"  [+] Added sample confirmed reservation for {rest.name} (Table {table.table_number})")
            db.session.commit()
            
        # 8. Seed Sample Completed Orders Across Restaurants
        if active_cust:
            for rest in Restaurant.query.filter_by(is_active=True).all():
                has_order = Order.query.filter_by(restaurant_id=rest.id).first()
                if not has_order:
                    first_item = MenuItem.query.filter_by(restaurant_id=rest.id, is_available=True).first()
                    if first_item:
                        sample_order = Order(
                            customer_id=active_cust.id,
                            restaurant_id=rest.id,
                            status='served',
                            total_amount=first_item.price * 2,
                            is_customer_confirmed=True
                        )
                        db.session.add(sample_order)
                        db.session.flush()
                        
                        item_line = OrderItem(
                            order_id=sample_order.id,
                            menu_item_id=first_item.id,
                            quantity=2,
                            unit_price=first_item.price,
                            subtotal=first_item.price * 2
                        )
                        db.session.add(item_line)
                        print(f"  [+] Added sample served order for {rest.name} (Rs. {sample_order.total_amount})")
            db.session.commit()
            
        print("\nDatabase seeding completed successfully!")
        
        # Print summary counts directly from MySQL
        print("\n=== Current MySQL smart_restaurant_db Table Row Counts ===")
        print(f"  users: {User.query.count()} rows")
        print(f"  restaurants: {Restaurant.query.count()} rows")
        print(f"  restaurant_staff: {RestaurantStaff.query.count()} rows")
        print(f"  tables: {Table.query.count()} rows")
        print(f"  menu_categories: {MenuCategory.query.count()} rows")
        print(f"  menu_items: {MenuItem.query.count()} rows")
        print(f"  reservations: {Reservation.query.count()} rows")
        print(f"  orders: {Order.query.count()} rows")
        print(f"  order_items: {OrderItem.query.count()} rows")

if __name__ == '__main__':
    seed_database()
