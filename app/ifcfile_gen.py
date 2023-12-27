import ifcopenshell



def create_ifc_file():
    ifc_file = ifcopenshell.file()

    project = ifc_file.createIfcProject(
        GlobalId=ifcopenshell.guid.new(), 
        OwnerHistory=None, 
        Name="Example Project", 
        Description=None, 
        ObjectType="Project", 
        LongName=None, 
        Phase=None, 
        RepresentationContexts=None, 
        UnitsInContext=None
    )


    with open("output.ifc", "wb") as file:
        file.write(ifc_file.wrapped_data.to_string())


def main():
    create_ifc_file()
    print('done')

if __name__ == "__main__":
    main()