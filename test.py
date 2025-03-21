# Test
link = "https://www.thewindows12.com/wp-content/uploads/2024/05/image-6.png"

if "/wp-content/uploads/" in link:
    relative_path = link.split('/wp-content/uploads/')[-1]
    print(f'images/post/{relative_path}')
# if link.startswith("https://www.thewindows12.com/wp-content/uploads/"):
#     relative_path = link.replace("https://www.thewindows12.com/wp-content/uploads/", "")
#     return f'images/post/{relative_path}'
else:
    print("Invalid link format.")