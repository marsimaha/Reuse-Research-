from flask import Flask, render_template, request, redirect, url_for, jsonify
import search as sh
import pandas as pd
import logging
from numpy import random
from flask import jsonify

import numpy as np
from urllib.parse import urlencode

from neo4j import GraphDatabase

URI = "neo4j+ssc://d4e7c69a.databases.neo4j.io"
AUTH = ("neo4j", "8gGwVhSx2-ycIPiPGOWejHAhufieq2XOOrkOAizxa1E")

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()

app = Flask(__name__)
logging.basicConfig(filename='app.log', level=logging.INFO)

# ... (the get_top_matches function and other necessary functions go here)

@app.route('/', methods=['GET', 'POST'])
def index():

    IFC = pd.read_csv("IFC_processed.csv") 
    adapter = pd.read_csv("adapter.csv") 

    if request.method == 'POST':
        data = request.get_json() 
        toggle_states = data.get('states', None)
        search_query = data.get('search_bar', None)
        check = True
 
        if toggle_states["IFC"] == True:
            mask = (IFC['raw'] == search_query)
            indices = IFC[mask].index.tolist()
            out = IFC.loc[indices, 'IFC'] 
            name = None 
            code = None 
            if not out.empty:
                name = out.reset_index().IFC[0]
                code = "IFC :" + search_query 
            else:
                print("No matching IFC found.")
            most_similar_text2 = [] 
            similar_texts = []  
            most_similar_text3 = [] 
            check = False
        # Search the dataset for the most similar texts
        else:
            results, cos = sh.get_query_matches(search_query, IFC['IFC'])
            cos = np.sort(cos)[[-1, -2, -3, -4, -5]]            
            if np.max(cos)>0.1:
                if np.all(cos[0]> max(cos[1:4]+0.2)):
                    results = [results[0]]
                    cos = [cos[0]]
                    similar_texts = np.unique(IFC.raw[results])
                else:
                    similar_texts = np.unique(IFC.raw[results]) 

                similar_texts = list(zip(similar_texts, cos))
                most_similar_text2 = sh.get_MF(adapter, results)
                most_similar_text3 = sh.get_eBKP(adapter, results)
                name = None
                code = None  
                check = True
            else:   
                return render_template('dbnotfound.html')
                
        response_data = {
            'check': check,
            'names': name,
            'code': code,
            'search_query': search_query,
            'similar_texts': similar_texts,
            'most_similar_text2': most_similar_text2,
            'most_similar_text3': most_similar_text3
        }
        print(response_data)
        return render_template('index.html',**response_data)

    return render_template('index.html')  


def get_components_with_same_name(driver, name):
    with driver.session() as session:  
        query = (
            "MATCH (c:Component {name: $name}) "
            "RETURN c"
        )
        result = session.run(query, name=name)
        components = [record['c'] for record in result]
        return components


@app.route('/post', methods=['GET', 'POST'])
def post():
    if request.method == 'POST':
        user = request.form['user']
        name = request.form['name']
        material = request.form['material']
        width = request.form['width']
        length = request.form['length']
        classification = request.form['classification']
        
        # Insert data into Neo4j
        with driver.session() as session:
            if classification == "":
                id = random.randint(100)
                IFC = pd.read_csv("IFC_processed.csv")
                results, cos = sh.get_query_matches(name, IFC['IFC'])
                results = [results]
                classification = IFC.raw[results[0][0]]
                session.run("CREATE (a:Component {id: $id,user: $user, name: $name, material: $material, length: $length, width: $width, classification: $classification})",
                            id=int(id), name=name, material=material,width=width, length=length, classification=classification, user = user)
            else:
                eBKP = pd.read_csv("eBKP_processed.csv")
                MF = pd.read_csv("MF_processed.csv")
                IFC = pd.read_csv("IFC_processed.csv")
                if classification in eBKP.code or classification in MF.code or classification in IFC.raw:
                    session.run("CREATE (a:Component {id: $id,user: $user, name: $name, material: $material, length: $length, width: $width, classification: $classification})",
                                id=int(id), name=name, material=material,width=width, length=length, classification=classification, user = user)
                else:
                    render_template('dbnotfound.html',)

        return redirect(url_for('read'))  # Updated this line
    
    return render_template('post.html')


# Define a function to fetch components with the same user value
def get_components_with_same_user(driver, user_value):
    with driver.session() as session:
        query = (
            "MATCH (c:Component {user: $user}) "
            "RETURN c"
        )
        result = session.run(query, user=user_value)
        components = [record['c'] for record in result]
        return components

def get_component_by_id(component_id):
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        with driver.session() as session:
            query = (
                "MATCH (c:Component) "
                "WHERE ID(c) = $id "
                "RETURN c"
            )
            result = session.run(query, id=component_id)
            record = result.single()
            if record:
                return record['c']
            else:
                return None
            

@app.route('/components', methods=['GET', 'POST'])
def read():
    components = []  # Initialize as an empty list

    if request.method == 'POST':
        user = request.form['user']

        # Fetch components only if user is not empty
        if user:
            components = get_components_with_same_user(driver, user)

    return render_template('components.html', components=components)

 
 
@app.route('/components/edit/<int:component_id>', methods=['GET', 'POST'])
def edit_component(component_id):
    component = get_component_by_id(component_id)

    if request.method == 'POST':
        length = request.form['length']
        name = request.form['name']
        material = request.form['material']

        width = request.form['width']
        classification = request.form['classification']

        # Prepare a dictionary to hold the updated properties
        updated_properties = {}
        
        if classification != "":
            updated_properties['classification'] = classification
        if width != "":
            updated_properties['width'] = width
        if length != "":
            updated_properties['length'] = length
        if material != "":
            updated_properties['material'] = material
        if name != "":
            updated_properties['name'] = name

        # Calculate the mean length and width for components with the same name in Neo4j
        if name:
            components_with_same_name = get_components_with_same_name(driver, name)
            if components_with_same_name:
                lengths = [float(comp['length']) if comp['length'] != "" else np.nan for comp in components_with_same_name]
                widths = [float(comp['width']) if comp['width'] != "" else np.nan for comp in components_with_same_name]
                if lengths:
                    updated_properties['length'] = str(np.nanmean(lengths))
                if widths:
                    updated_properties['width'] = str(np.nanmean(widths))

        if updated_properties:
            # Use a Cypher query to update the node's properties
            IFC = pd.read_csv("IFC_processed.csv")
            results, cos = sh.get_query_matches(name, IFC['IFC'])
            results = [results]
            updated_properties['classification'] = IFC.raw[results[0][0]]
            with driver.session() as session:
                query = (
                    "MATCH (c:Component) "
                    "WHERE ID(c) = $id "
                    "SET c += $props"
                )
                session.run(query, id=component_id, props=updated_properties)

        # Redirect to the component details page or another appropriate page
        return redirect(url_for('read'))

    return render_template('edit_component.html', component=component)

 
if __name__ == '__main__': 
    # APP.run(host='0.0.0.0', port=5000, debug=True)  
    app.run(debug=True) 
 
  