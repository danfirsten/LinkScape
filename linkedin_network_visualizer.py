import pandas as pd
import networkx as nx
from pyvis.network import Network
import logging
import os
import random

# Set random seed for reproducibility
random.seed(42)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # Load your LinkedIn connections CSV file, skipping the notes section
    logger.info("Loading CSV file...")
    df = pd.read_csv("Connections.csv", skiprows=2)
    logger.info(f"Successfully loaded {len(df)} connections")

    # Initialize graph
    logger.info("Initializing graph...")
    G = nx.Graph()

    # Add nodes
    logger.info("Adding nodes to graph...")
    node_count = 0
    for i, row in df.iterrows():
        try:
            # Combine first and last name
            full_name = f"{row['First Name']} {row['Last Name']}"
            
            # Handle NaN values in Position and Company
            position = row.get('Position', '')
            company = row.get('Company', '')
            
            # Convert NaN to empty string
            if pd.isna(position):
                position = ''
            if pd.isna(company):
                company = ''
            
            # Create tooltip with both position and company
            tooltip = []
            if position:
                tooltip.append(f"Position: {position}")
            if company:
                tooltip.append(f"Company: {company}")
            tooltip_text = " | ".join(tooltip) if tooltip else "No additional information"
                
            G.add_node(full_name, 
                      title=tooltip_text,  # Combined tooltip
                      company=str(company))  # Keep company for edge creation
            node_count += 1
        except Exception as e:
            logger.error(f"Error adding node for row {i}: {str(e)}")
            logger.error(f"Row data: {row.to_dict()}")

    logger.info(f"Successfully added {node_count} nodes to the graph")

    # Add edges for people from the same company
    logger.info("Adding edges between connections at the same company...")
    edge_count = 0
    companies = df.groupby('Company')
    company_count = 0
    
    for company, group in companies:
        if pd.isna(company) or company == '':  # Skip empty company names
            logger.warning(f"Skipping {len(group)} connections with empty company names")
            continue
            
        company_count += 1
        names = [f"{row['First Name']} {row['Last Name']}" for _, row in group.iterrows()]
        logger.debug(f"Processing company: {company} with {len(names)} connections")
        
        for i in range(len(names)):
            for j in range(i+1, len(names)):
                try:
                    G.add_edge(names[i], names[j], relation='same_company')
                    edge_count += 1
                except Exception as e:
                    logger.error(f"Error adding edge between {names[i]} and {names[j]}: {str(e)}")

    logger.info(f"Processed {company_count} companies")
    logger.info(f"Added {edge_count} edges to the graph")

    # Create network visualization
    logger.info("Creating network visualization...")
    net = Network(notebook=False, height='800px', width='100%', bgcolor='#222222', font_color='white')
    
    # Configure node appearance and physics
    net.set_options("""
    var options = {
        "nodes": {
            "font": {
                "size": 12,
                "face": "arial"
            },
            "shape": "dot",
            "size": 20
        },
        "edges": {
            "color": {
                "inherit": true
            },
            "smooth": false
        },
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -50,
                "centralGravity": 0.01,
                "springLength": 100,
                "springConstant": 0.08,
                "damping": 0.4,
                "avoidOverlap": 1
            },
            "maxVelocity": 50,
            "solver": "forceAtlas2Based",
            "timestep": 0.35,
            "stabilization": {
                "enabled": true,
                "iterations": 2000,
                "updateInterval": 25,
                "onlyDynamicEdges": false,
                "fit": true
            }
        },
        "layout": {
            "improvedLayout": true,
            "randomSeed": 42
        }
    }
    """)
    
    net.from_nx(G)
    
    # Save the visualization
    logger.info("Saving visualization to linkedin_network.html...")
    try:
        # First try the standard method
        net.save_graph("linkedin_network.html")
    except Exception as e:
        logger.warning(f"Standard save method failed: {str(e)}")
        logger.info("Trying alternative save method...")
        try:
            # Alternative method using write_html
            net.write_html("linkedin_network.html", notebook=False)
        except Exception as e:
            logger.error(f"Alternative save method failed: {str(e)}")
            raise

    logger.info("Visualization complete!")

    # Print some statistics
    logger.info("\nNetwork Statistics:")
    logger.info(f"Total nodes: {G.number_of_nodes()}")
    logger.info(f"Total edges: {G.number_of_edges()}")
    logger.info(f"Number of companies: {company_count}")
    logger.info(f"Average connections per company: {edge_count/company_count:.2f}")

    # Verify the file was created
    if os.path.exists("linkedin_network.html"):
        logger.info("Successfully created linkedin_network.html")
    else:
        logger.error("Failed to create linkedin_network.html")

except Exception as e:
    logger.error(f"An error occurred: {str(e)}", exc_info=True)