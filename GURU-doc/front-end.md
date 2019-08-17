# CVAT Front-end Development (Old UI)

Since a newer version of front-end is currently in development, this document is aimed for structural improvement based on the old CVAT UI front-end framework. The first part of this developer guide to CVAT UI will provide insights on how front-end communicates with the server and render different annotation shapes onto the screen. The second part of the guide will demonstrate how we modified major files in order to achieve one specific feature for our research project: drawing and displaying fixation from user gaze data. 

## Front-End Structure (Annotations)

In order to render annotations, three steps are taken place in the procedure:
- API calls: UI requests data from the server. 
- Construct annotation collections: preprocessing data from the server into shape configurations
- Render annotation shapes: using configurations in collection, render the shape on the screen


## Specific Modification (Gaze Annotation)
