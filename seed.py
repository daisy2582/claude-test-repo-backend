"""Seed the database with sample data for development."""
from app.database import SessionLocal, engine, Base
from app.models import User, Post, PostCategory, Comment, Vote
from app.auth import hash_password

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # Check if already seeded
    if db.query(User).first():
        print("Database already has data. Skipping seed.")
        exit(0)

    # Create users
    users_data = [
        {"username": "greenqueen", "email": "green@example.com", "display_name": "Green Queen", "bio": "Plant-based chef & animal advocate"},
        {"username": "veganrunner", "email": "runner@example.com", "display_name": "Vegan Runner", "bio": "Marathon runner fueled by plants"},
        {"username": "plantdad", "email": "plantdad@example.com", "display_name": "Plant Dad", "bio": "Growing veggies & cooking them too"},
        {"username": "tofulover", "email": "tofu@example.com", "display_name": "Tofu Lover", "bio": "Tofu in every form, every day"},
        {"username": "earthmama", "email": "earth@example.com", "display_name": "Earth Mama", "bio": "Sustainability advocate & home cook"},
    ]

    users = []
    for u in users_data:
        user = User(
            username=u["username"],
            email=u["email"],
            display_name=u["display_name"],
            bio=u["bio"],
            hashed_password=hash_password("password123"),
        )
        db.add(user)
        users.append(user)
    db.flush()

    # Create posts
    posts_data = [
        {
            "title": "My 1-Year Vegan Anniversary! Here's What Changed",
            "content": "One year ago today, I made the switch to a fully plant-based lifestyle. Here's what I've noticed:\n\n- More energy throughout the day\n- Clearer skin than I've had in years\n- Lost 15 lbs without even trying\n- My grocery bill actually went DOWN\n- I discovered so many amazing foods I never would have tried\n\nThe first month was the hardest - I missed cheese the most. But once I found good cashew cheese recipes, I never looked back. If you're thinking about going vegan, just START. You don't have to be perfect from day one.",
            "category": PostCategory.JOURNEY,
            "author_idx": 0, "upvotes": 142, "downvotes": 3, "comment_count": 2,
        },
        {
            "title": "Ultimate Crispy Tofu - The Secret is Cornstarch!",
            "content": "I've been perfecting crispy tofu for months and finally cracked it:\n\n1. Press tofu for 30 min (use heavy books!)\n2. Cut into cubes\n3. Toss in cornstarch + salt + garlic powder\n4. Air fry at 400F for 15 min, shaking halfway\n5. Toss in your favorite sauce\n\nThe cornstarch is the GAME CHANGER. It creates this incredible crispy shell while keeping the inside tender. My non-vegan friends couldn't believe it was tofu!",
            "category": PostCategory.RECIPE,
            "author_idx": 3, "upvotes": 89, "downvotes": 2, "comment_count": 1,
        },
        {
            "title": "Tip: How to get enough protein on a vegan diet",
            "content": "The #1 question I get asked is 'where do you get your protein?' Here's my daily breakdown:\n\nBreakfast: Overnight oats with hemp seeds + PB (20g)\nLunch: Chickpea salad wrap (18g)\nSnack: Edamame (17g)\nDinner: Lentil curry with rice (22g)\nTotal: ~77g protein\n\nOther high-protein vegan foods:\n- Tempeh (31g per cup)\n- Seitan (75g per 100g!)\n- Black beans (15g per cup)\n- Quinoa (8g per cup)\n\nYou do NOT need protein powder. Whole foods have you covered!",
            "category": PostCategory.TIP,
            "author_idx": 1, "upvotes": 234, "downvotes": 8, "comment_count": 1,
        },
        {
            "title": "Week 3 Progress: Down 8lbs and feeling amazing!",
            "content": "Started my plant-based journey 3 weeks ago after watching Dominion. I'm down 8 lbs, my blood pressure dropped from 140/90 to 125/82, and I have way more energy.\n\nBiggest wins this week:\n- Made my first homemade seitan (it was actually good!)\n- Found an amazing vegan restaurant in my city\n- My partner tried my cooking and wants to join me!\n\nBiggest challenge: Social situations. Went to a BBQ and there was literally nothing I could eat. Next time I'm bringing my own food.\n\nKeep going everyone, it gets easier!",
            "category": PostCategory.PROGRESS,
            "author_idx": 4, "upvotes": 67, "downvotes": 1, "comment_count": 1,
        },
        {
            "title": "The dairy industry doesn't want you to see this",
            "content": "Just learned that dairy cows are forcibly impregnated every year and their calves are taken away within hours of birth. The mothers cry for days. Male calves are often sent to veal farms.\n\nA single glass of dairy milk requires 1000 liters of water to produce. Oat milk? Just 48 liters.\n\nEvery time you choose plant milk, you're voting with your wallet for a kinder world. Small choices, big impact.\n\nHere are some great resources if you want to learn more:\n- Dominion (documentary)\n- Earthlings (documentary)\n- 'Eating Animals' by Jonathan Safran Foer",
            "category": PostCategory.DISCUSSION,
            "author_idx": 0, "upvotes": 312, "downvotes": 45, "comment_count": 1,
        },
        {
            "title": "5-Minute Peanut Noodles (Student Budget Friendly!)",
            "content": "This costs about $2 per serving and takes 5 minutes:\n\nIngredients:\n- 1 pack ramen noodles (discard seasoning)\n- 2 tbsp peanut butter\n- 1 tbsp soy sauce\n- 1 tsp sriracha\n- Squeeze of lime\n- Optional: frozen veggies, green onions\n\nCook noodles. Mix PB + soy sauce + sriracha + lime in bowl. Drain noodles, toss in sauce. Done!\n\nI ate this 3x a week in college and never got tired of it. Cheap, fast, delicious, vegan!",
            "category": PostCategory.RECIPE,
            "author_idx": 2, "upvotes": 178, "downvotes": 4, "comment_count": 1,
        },
        {
            "title": "New vegan cheese at Trader Joe's is INCREDIBLE",
            "content": "Has anyone tried the new cashew-based mozzarella at TJ's? It actually MELTS properly on pizza! I'm shook.\n\nI've tried probably 20 different vegan cheeses over the past 2 years and this is hands down the best one for pizza. It browns, it stretches, and it actually tastes like cheese.\n\nIt's $4.99 for a block. I bought 5 of them because I'm afraid they'll discontinue it (as TJ's does with all good things).\n\nWhat's your favorite vegan cheese? Drop recommendations below!",
            "category": PostCategory.NEWS,
            "author_idx": 3, "upvotes": 95, "downvotes": 7, "comment_count": 1,
        },
    ]

    posts = []
    for p in posts_data:
        post = Post(
            title=p["title"],
            content=p["content"],
            category=p["category"],
            author_id=users[p["author_idx"]].id,
            upvotes=p["upvotes"],
            downvotes=p["downvotes"],
            comment_count=p["comment_count"],
        )
        db.add(post)
        posts.append(post)
    db.flush()

    # Add some comments
    comments_data = [
        {"content": "Congratulations on your 1 year! I'm at month 3 and this gives me so much motivation!", "author_idx": 4, "post_idx": 0},
        {"content": "The cheese part is SO real. Cashew cheese changed the game for me too!", "author_idx": 3, "post_idx": 0},
        {"content": "Just tried this and OMG. The cornstarch trick works perfectly!", "author_idx": 0, "post_idx": 1},
        {"content": "Saving this post! I'm so tired of the protein question lol", "author_idx": 4, "post_idx": 2},
        {"content": "Keep going! The social situations get easier, I promise. I always bring a dish to share now.", "author_idx": 0, "post_idx": 3},
        {"content": "Everyone needs to watch Dominion. Changed my life.", "author_idx": 1, "post_idx": 4},
        {"content": "Making this tonight! Sounds perfect for lazy weeknight dinners.", "author_idx": 4, "post_idx": 5},
        {"content": "I need to find this cheese ASAP. Is it in the refrigerated section?", "author_idx": 2, "post_idx": 6},
    ]

    for c in comments_data:
        comment = Comment(
            content=c["content"],
            author_id=users[c["author_idx"]].id,
            post_id=posts[c["post_idx"]].id,
        )
        db.add(comment)

    db.commit()
    print(f"Seeded {len(users)} users, {len(posts)} posts, and {len(comments_data)} comments.")
    print("\nSample login credentials:")
    print("  Username: greenqueen | Password: password123")
    print("  Username: veganrunner | Password: password123")

except Exception as e:
    db.rollback()
    print(f"Error seeding: {e}")
    raise
finally:
    db.close()
