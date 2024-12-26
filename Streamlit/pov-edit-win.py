# POV-Ray Scene Editor with Streamlit UI
# This application provides a web interface for creating and editing POV-Ray scenes,
# with support for multiple objects, textures, lighting, and camera controls.

import streamlit as st
import subprocess
import os
from pathlib import Path
import tempfile
from PIL import Image
import json
from datetime import datetime

# Pre-defined demo scenes showcasing different setups and object arrangements
DEMO_SCENES = {
    "Three Platonic Solids": {
        "camera": {"location": (8, 6, -10), "look_at": (0, 0, 0)},
        "lights": [
            # Main key light
            {"position": (10, 10, -10), "color": (1, 1, 1), "intensity": 1.0},
            # Fill light with slight blue tint
            {"position": (-8, 5, -8), "color": (0.5, 0.5, 0.6), "intensity": 0.6}
        ],
        "objects": [
            # Red chrome sphere
            {
                "obj_type": "sphere", "position": (-2, 0, 0),
                "rotation": (0, 0, 0), "scale": (1, 1, 1),
                "color": (0.8, 0.2, 0.2), "texture": "Chrome_Metal"
            },
            # Green aluminum box
            {
                "obj_type": "box", "position": (2, 0, 0),
                "rotation": (45, 45, 0), "scale": (1, 1, 1),
                "color": (0.2, 0.8, 0.2), "texture": "Brushed_Aluminum"
            },
            # Blue glass cone
            {
                "obj_type": "cone", "position": (0, 2, 0),
                "rotation": (0, 0, 0), "scale": (1, 2, 1),
                "color": (0.2, 0.2, 0.8), "texture": "Glass"
            }
        ]
    },
    "Studio Setup": {
        "camera": {"location": (0, 5, -15), "look_at": (0, 0, 0)},
        "lights": [
            # Main key light with warm tint
            {"position": (10, 10, -5), "color": (1, 0.9, 0.8), "intensity": 0.8},
            # Fill light with cool tint
            {"position": (-8, 8, -8), "color": (0.8, 0.8, 1), "intensity": 0.6},
            # Rim light
            {"position": (0, 3, -12), "color": (1, 1, 1), "intensity": 0.3}
        ],
        "objects": []
    }
}

# Available textures from POV-Ray standard includes
TEXTURES = {
    "None": None,
    "Chrome_Metal": "Chrome_Metal",
    "Glass": "Glass",
    "Brushed_Aluminum": "Brushed_Aluminum",
    "Brass_Metal": "Brass_Metal",
    "Copper_Metal": "Copper_Metal",
    "Gold_Metal": "Gold_Metal",
    "Silver_Metal": "Silver_Metal",
    "Polished_Chrome": "Polished_Chrome",
    "Mirror": "Mirror"
}

class PovrayObject:
    """
    Represents a single object in the POV-Ray scene with properties for
    position, rotation, scale, color, and texture.
    """
    def __init__(self, obj_type, position=(0,0,0), rotation=(0,0,0), 
                 scale=(1,1,1), color=(1,1,1), texture=None):
        self.obj_type = obj_type
        self.position = position
        self.rotation = rotation
        self.scale = scale
        self.color = color
        self.texture = texture
    
    def to_pov(self):
        """
        Convert the object to POV-Ray scene description language syntax
        Returns: String containing POV-Ray code for this object
        """
        pov_str = f"object {{\n"
        pov_str += f"    {self.obj_type}\n"
        pov_str += f"    translate <{self.position[0]}, {self.position[1]}, {self.position[2]}>\n"
        pov_str += f"    rotate <{self.rotation[0]}, {self.rotation[1]}, {self.rotation[2]}>\n"
        pov_str += f"    scale <{self.scale[0]}, {self.scale[1]}, {self.scale[2]}>\n"
        
        if self.texture:
            pov_str += f"    texture {{ {self.texture} }}\n"
        else:
            pov_str += f"    pigment {{ color rgb <{self.color[0]}, {self.color[1]}, {self.color[2]}> }}\n"
        
        pov_str += "}\n"
        return pov_str
    
    def to_dict(self):
        """Convert object properties to dictionary for serialization"""
        return {
            "obj_type": self.obj_type,
            "position": self.position,
            "rotation": self.rotation,
            "scale": self.scale,
            "color": self.color,
            "texture": self.texture
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create object instance from dictionary data"""
        return cls(**data)

class PovrayScene:
    """
    Represents a complete POV-Ray scene containing objects, camera settings,
    and light sources.
    """
    def __init__(self):
        self.objects = []
        self.camera = {
            'location': (0, 0, -10),
            'look_at': (0, 0, 0)
        }
        self.lights = []
    
    def add_object(self, obj):
        """Add a new object to the scene"""
        self.objects.append(obj)
    
    def add_light(self, position, color=(1,1,1), intensity=1.0):
        """Add a new light source to the scene"""
        self.lights.append({
            'position': position,
            'color': color,
            'intensity': intensity
        })
    
    def generate_scene(self):
        """
        Generate complete POV-Ray scene file content including all necessary
        includes, camera setup, lights, and objects
        Returns: String containing complete POV-Ray scene code
        """
        # Include standard POV-Ray library files
        scene = "#include \"colors.inc\"\n"
        scene += "#include \"textures.inc\"\n"
        scene += "#include \"metals.inc\"\n"
        scene += "#include \"glass.inc\"\n\n"
        
        # Global settings for ambient lighting
        scene += "global_settings { ambient_light rgb<0.1, 0.1, 0.1> }\n\n"
        
        # Camera setup
        scene += f"""camera {{
    location <{self.camera['location'][0]}, {self.camera['location'][1]}, {self.camera['location'][2]}>
    look_at <{self.camera['look_at'][0]}, {self.camera['look_at'][1]}, {self.camera['look_at'][2]}>
}}\n\n"""
        
        # Light sources
        for light in self.lights:
            pos = light['position']
            col = light['color']
            scene += f"""light_source {{
    <{pos[0]}, {pos[1]}, {pos[2]}>
    color rgb <{col[0]}, {col[1]}, {col[2]}>
    intensity {light['intensity']}
}}\n\n"""
        
        # Scene objects
        for obj in self.objects:
            scene += obj.to_pov() + "\n"
        
        return scene
    
    def to_dict(self):
        """Convert scene to dictionary for serialization"""
        return {
            "camera": self.camera,
            "lights": self.lights,
            "objects": [obj.to_dict() for obj in self.objects]
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create scene instance from dictionary data"""
        scene = cls()
        scene.camera = data["camera"]
        scene.lights = data["lights"]
        scene.objects = [PovrayObject.from_dict(obj_data) for obj_data in data["objects"]]
        return scene

def render_povray(scene_content, output_path):
    """
    Render POV-Ray scene and save the result
    Args:
        scene_content: String containing POV-Ray scene code
        output_path: Path where the rendered image should be saved
    Returns:
        Path to rendered image or None if rendering failed
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pov', delete=False) as temp_file:
        temp_file.write(scene_content)
        scene_file = temp_file.name
    
    try:
        # Run POV-Ray with anti-aliasing and other quality settings
        povray_path = r"C:\Program Files\POV-Ray\v3.7\bin\pvengine64.exe"
        subprocess.run([povray_path, f'+I{scene_file}', f'+O{output_path}',
                       '+W800', '+H600', '+A', '+AM2', '-D'], 
                      check=True, capture_output=True, shell=True)
        return output_path
    except subprocess.CalledProcessError as e:
        st.error(f"Error rendering scene: {e.stderr.decode()}")
        return None
    finally:
        os.unlink(scene_file)

def save_scene(scene, filename):
    """Save scene to JSON file"""
    with open(filename, 'w') as f:
        json.dump(scene.to_dict(), f, indent=2)

def load_scene(filename):
    """Load scene from JSON file"""
    with open(filename, 'r') as f:
        data = json.load(f)
    return PovrayScene.from_dict(data)

def main():
    """Main application entry point setting up the Streamlit UI"""
    st.title("POV-Ray Scene Editor")
    
    # Initialize or get existing scene from session state
    if 'scene' not in st.session_state:
        st.session_state.scene = PovrayScene()
    
    # Demo scene selector
    demo_scene = st.selectbox("Load Demo Scene", ["Custom"] + list(DEMO_SCENES.keys()))
    if demo_scene != "Custom" and st.button("Load Demo"):
        st.session_state.scene = PovrayScene.from_dict(DEMO_SCENES[demo_scene])
    
    # Sidebar for object controls
    with st.sidebar:
        st.header("Scene Objects")
        
        # Object creation controls
        st.subheader("Add New Object")
        obj_type = st.selectbox("Object Type", 
                              ["sphere", "box", "cylinder", "cone", "torus"])
        
        # Split controls into two columns for better layout
        col1, col2 = st.columns(2)
        with col1:
            st.text("Position")
            pos_x = st.slider("X Pos", -10.0, 10.0, 0.0, step=0.1)
            pos_y = st.slider("Y Pos", -10.0, 10.0, 0.0, step=0.1)
            pos_z = st.slider("Z Pos", -10.0, 10.0, 0.0, step=0.1)
            
            st.text("Color")
            color_r = st.slider("Red", 0.0, 1.0, 1.0, step=0.01)
            color_g = st.slider("Green", 0.0, 1.0, 1.0, step=0.01)
            color_b = st.slider("Blue", 0.0, 1.0, 1.0, step=0.01)
        
        with col2:
            st.text("Rotation")
            rot_x = st.slider("X Rot", 0.0, 360.0, 0.0, step=1.0)
            rot_y = st.slider("Y Rot", 0.0, 360.0, 0.0, step=1.0)
            rot_z = st.slider("Z Rot", 0.0, 360.0, 0.0, step=1.0)
            
            st.text("Scale")
            scale_x = st.slider("X Scale", 0.1, 5.0, 1.0, step=0.1)
            scale_y = st.slider("Y Scale", 0.1, 5.0, 1.0, step=0.1)
            scale_z = st.slider("Z Scale", 0.1, 5.0, 1.0, step=0.1)
        
        # Texture selector
        texture = st.selectbox("Texture", list(TEXTURES.keys()))
        
        # Add object button
        if st.button("Add Object"):
            new_obj = PovrayObject(
                obj_type,
                position=(pos_x, pos_y, pos_z),
                rotation=(rot_x, rot_y, rot_z),
                scale=(scale_x, scale_y, scale_z),
                color=(color_r, color_g, color_b),
                texture=TEXTURES[texture]
            )
            st.session_state.scene.add_object(new_obj)
    
    # Main area tabs
    tab1, tab2, tab3 = st.tabs(["Scene View", "Camera & Lights", "Save/Load"])
    
    with tab1:
        # Scene code display and render controls
        scene_code = st.session_state.scene.generate_scene()
        st.text_area("Scene Code", scene_code, height=200)
        
        if st.button("Render Scene"):
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_output:
                output_path = tmp_output.name
            
            rendered_path = render_povray(scene_code, output_path)
            if rendered_path:
                try:
                    image = Image.open(rendered_path)
                    st.image(image, caption="Rendered Scene")
                finally:
                    os.unlink(rendered_path)
    
    with tab2:
        # Camera controls
        st.subheader("Camera Settings")
        cam_col1, cam_col2 = st.columns(2)
        
        with cam_col1:
            st.text("Camera Location")
            cam_x = st.slider("Cam X", -20.0, 20.0, 
                            float(st.session_state.scene.camera['location'][0]),
                            step=0.1)
            cam_y = st.slider("Cam Y", -20.0, 20.0, 
                            st.session_state.scene.camera['location'][1])
            cam_z = st.slider("Cam Z", -20.0, 20.0, 
                            st.session_state.scene.camera['location'][2])
        
        with cam_col2:
            st.text("Look At Point")
            look_x = st.slider("Look X", -20.0, 20.0, 
                             st.session_state.scene.camera['look_at'][0])
            look_y = st.slider("Look Y", -20.0, 20.0, 
                             st.session_state.scene.camera['look_at'][1])
            look_z = st.slider("Look Z", -20.0, 20.0, 
                             st.session_state.scene.camera['look_at'][2])
        
        if st.button("Update Camera"):
            st.session_state.scene.camera = {
                'location': (cam_x, cam_y, cam_z),
                'look_at': (look_x, look_y, look_z)
            }
        
        # Light controls
        st.subheader("Lights")
        if st.button("Add Light"):
            st.session_state.scene.add_light((5, 5, -5))
        
        # Controls for each light in the scene
        for i, light in enumerate(st.session_state.scene.lights):
            st.text(f"Light {i+1}")
            light_col1, light_col2 = st.columns(2)
            
            with light_col1:
                pos = list(light['position'])
                light['position'] = (
                    st.slider(f"Light {i+1} X", min_value=-20.0, max_value=20.0, value=float(pos[0]), step=0.1),
                    st.slider(f"Light {i+1} Y", min_value=-20.0, max_value=20.0, value=float(pos[1]), step=0.1),
                    st.slider(f"Light {i+1} Z", min_value=-20.0, max_value=20.0, value=float(pos[2]), step=0.1)
                )
            
            with light_col2:
                light['intensity'] = st.slider(f"Light {i+1} Intensity", 
                                            min_value=0.0, max_value=2.0, value=float(light['intensity']), step=0.1)
                light['color'] = (
                    st.slider(f"Light {i+1} R", 0.0, 1.0, light['color'][0]),
                    st.slider(f"Light {i+1} G", 0.0, 1.0, light['color'][1]),
                    st.slider(f"Light {i+1} B", 0.0, 1.0, light['color'][2])
                )
    
    with tab3:
        # Save/Load functionality
        st.subheader("Save/Load Scene")
        
        # Save current scene
        save_name = st.text_input("Scene Name", 
            value=f"scene_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        if st.button("Save Scene"):
            save_scene(st.session_state.scene, f"{save_name}.json")
            st.success(f"Scene saved as {save_name}.json")
        
        # Load existing scene
        uploaded_file = st.file_uploader("Load Scene", type="json")
        if uploaded_file is not None:
            content = uploaded_file.read()
            with tempfile.NamedTemporaryFile(mode='wb', delete=False) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name
            
            try:
                st.session_state.scene = load_scene(temp_path)
                st.success("Scene loaded successfully")
            except Exception as e:
                st.error(f"Error loading scene: {str(e)}")
            finally:
                os.unlink(temp_path)

if __name__ == "__main__":
    main()