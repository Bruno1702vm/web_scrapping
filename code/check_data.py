import pandas as pd

posts = pd.read_csv("output/posts.csv")
comments = pd.read_csv("output/comments.csv")

print("=== POSTS ===")
print("Filas:", len(posts))
print(posts["subreddit"].value_counts())
print("post_id únicos:", posts["post_id"].nunique())

print("\n=== COMMENTS ===")
print("Filas:", len(comments))
print("comment_id únicos:", comments["comment_id"].nunique())

# Comentarios con post_id válido
valid_post_ids = set(posts["post_id"])
invalid = comments[~comments["post_id"].isin(valid_post_ids)]
print("\nComentarios con post_id inválido:", len(invalid))

# Nulos básicos
print("\nNulos en posts:\n", posts.isna().sum())
print("\nNulos en comments:\n", comments.isna().sum())

# Vista rápida de 3 filas de cada uno
print("\nMuestra posts:\n", posts.head(3))
print("\nMuestra comments:\n", comments.head(3))
