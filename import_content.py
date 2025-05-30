def import_blog_from_mariadb():
    """Import blog posts from MariaDB to Django"""
    print(f"\n📝 Blog Import Section")
    print("=" * 30)
    
    # Import blog models
    from blog.models import Post, Category as BlogCategory
    
    # Step 1: Show current Django blog state
    print(f"\n📝 Current Django Blog Posts:")
    django_posts = Post.objects.all()
    print(f"Found {django_posts.count()} blog posts in Django")
    for post in django_posts:
        print(f"  • {post.title}: {len(post.content)} chars")
    
    # Step 2: Connect to MariaDB and get blog content
    print(f"\n🔍 Getting blog posts from MariaDB...")
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='aim_temp',
            user='aim_temp_user',
            password='temp_password123'
        )
        cursor = connection.cursor(dictionary=True)
        
        # Get blog posts with content
        cursor.execute("""
            SELECT id, title, slug, content, status, featured, 
                   publish_date, meta_title, meta_description, category_id
            FROM blog_post
            WHERE content IS NOT NULL AND content != '' AND LENGTH(content) > 100
            ORDER BY id
        """)
        
        mariadb_posts = cursor.fetchall()
        print(f"Found {len(mariadb_posts)} blog posts with content in MariaDB:")
        
        for post in mariadb_posts:
            print(f"  • {post['title']}: {len(post['content'])} chars (ID: {post['id']})")
        
        # Step 3: Import blog posts
        print(f"\n🔧 Creating blog posts in Django...")
        created_count = 0
        
        for mariadb_post in mariadb_posts:
            try:
                # Check if post already exists by title
                existing_post = Post.objects.filter(title=mariadb_post['title']).first()
                if existing_post:
                    print(f"⚠️  Post already exists: {mariadb_post['title']}")
                    continue
                
                # Get or create a default category
                category = None
                if mariadb_post['category_id']:
                    # Try to find category or create a default one
                    category, created = BlogCategory.objects.get_or_create(
                        name='General',
                        defaults={'slug': 'general', 'description': 'General blog posts'}
                    )
                
                # Create new blog post
                new_post = Post.objects.create(
                    title=mariadb_post['title'],
                    slug=mariadb_post['slug'],
                    content=mariadb_post['content'],
                    status=mariadb_post['status'],
                    is_featured=bool(mariadb_post['featured']),
                    publish_date=mariadb_post['publish_date'],
                    category=category
                )
                
                created_count += 1
                print(f"✅ Created: {new_post.title} ({len(new_post.content)} chars)")
                    
            except Exception as e:
                print(f"❌ Error creating post {mariadb_post['title']}: {e}")
                continue
        
        cursor.close()
        connection.close()
        
        # Step 4: Final verification
        print(f"\n📊 Blog Import Complete!")
        print(f"✅ Created {created_count} blog posts")
        
        print(f"\n🔍 Final Blog Verification:")
        for post in Post.objects.all().order_by('title'):
            content_length = len(post.content)
            has_content = content_length > 100
            status = "✅ HAS CONTENT" if has_content else "❌ NO CONTENT"
            print(f"  • {post.title}: {content_length} chars - {status}")
            
    except Exception as e:
        print(f"❌ Blog import error: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🚀 Final Content Import - Documentation + Blog")
    print("=" * 60)
    
    # Import documentation (your existing code)
    # ... existing documentation import code ...
    
    # Import blog posts
    import_blog_from_mariadb()
    
    print(f"\n🎉 ALL IMPORTS COMPLETE!")
    print(f"1. Check Django admin: https://aimarketingplatform.app/admin/")
    print(f"2. Documentation: /admin/docs/documentationpage/")
    print(f"3. Blog: /admin/blog/post/")
    print(f"4. Your Friday evening awaits! 🍻")