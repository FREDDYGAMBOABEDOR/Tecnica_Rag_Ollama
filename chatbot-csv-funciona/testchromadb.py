import chromadb

client = chromadb.Client()

collection = client.create_collection("all-my-documents")

collection.add(
    documents=[
        "La empresa Lostsys se dedica a ofrecer servícios y productos a empresas sobre informática corporativa como software de gestión, CRMs, ERPs, portales corporativos, eCommerce, formación, DevOps, etc.",
        "En Lostsys podemos ayudarte ha mejorar tus procesos de CI/CD con nuestros productos y servícios de DevOps.",
        "En Lostsys podemos ayudarte a digitalizarte con nuestros servícios de desarrollo de aplicaciones corporativas.",
        "En Lostsys te podemos entrenar y formar a múltiples áreas de la informática corporativa como desarrollo, Data, IA o DevOps.",
        "En Lostsys te podemos desarrollar una tienda online para vender por todo el mundo y mas allà.",
        "En Lostsys te podemos desarrollar un eCommerce para vender por todo el mundo y mas allà",
    ],
    ids=["id1", "id2","id3", "id4","id5", "id6"]
)

results = collection.query(
    query_texts=["necesito formación"], 
    n_results=2 
)

print(results)
