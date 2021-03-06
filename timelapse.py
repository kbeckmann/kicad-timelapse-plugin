import pcbnew
import os
import re
import shutil
import sys
from timer import RepeatedTimer
from svg_processor import SvgProcessor
import sched, time
capture_interval=10

# Renders back-to-front
layers = [
    {
        'layer': pcbnew.B_Cu,
        'name' : 'B_Cu',
        'color': '#008400',
        'alpha': 0.5,
    },
    {
        'layer': pcbnew.In4_Cu,
        'name' : 'In4_Cu',
        'color': '#000084',
        'alpha': 0.5,
    },
    {
        'layer': pcbnew.In3_Cu,
        'name' : 'In3_Cu',
        'color': '#C20000',
        'alpha': 0.5,
    },
    {
        'layer': pcbnew.In2_Cu,
        'name' : 'In2_Cu',
        'color': '#C200C2',
        'alpha': 0.5,
    },
    {
        'layer': pcbnew.In1_Cu,
        'name' : 'In1_Cu',
        'color': '#C2C200',
        'alpha': 0.5,
    },
    {
        'layer': pcbnew.F_Cu,
        'name' : 'F_Cu',
        'color': '#840000',
        'alpha': 0.5,
    },
    {
        'layer': pcbnew.B_SilkS,
        'name' :'B_SilkS',
        'color': '#CC00CC',
        'alpha': 0.8,
    },
    {
        'layer': pcbnew.F_SilkS,
        'name' : 'F_SilkS',
        'color': '#00CCCC',
        'alpha': 0.8,
    },
    {
        'layer': pcbnew.Cmts_User,
        'name' : 'Cmts_User',
        'color': '#333333',
        'alpha': 0.8,
    },
    {
        'layer': pcbnew.Edge_Cuts,
        'name' : 'Edge_Cuts',
        'color': '#3333CC',
        'alpha': 0.8,
    },
]

def static_var(varname, value):
    def decorate(func):
        setattr(func, varname, value)
        return func
    return decorate

def extract_biggest_number(files):
    numbers=[]
    regex = re.compile(r'(\d+)\.svg$')
    for sFile in files:
        print("found file:"+sFile)
        extracted_nums=regex.findall(sFile)
        if extracted_nums:
            print("Recognised num:"+str(extracted_nums))
            numbers.append(extracted_nums[0])
    return int(max(numbers)) if numbers else 0


class SimplePlugin(pcbnew.ActionPlugin):
    def __Init__(self):
        self.board=pcbnew.GetBoard()
    def defaults(self):
        self.name = "Timelapse recorder"
        self.category = "A descriptive category name"
        self.description = "A description of the plugin and what it does"

    def screenshot(self):
        print("Taking a screenshot")
        self.board = pcbnew.GetBoard()
        board_path=self.board.GetFileName()

        # There doesn't seem to be a clean way to detect when KiCad is shutting down.
        # Check for an empty board path and return False to signal that the timer should not restart.
        if board_path == "":
            print("Shutting down")
            return False

        board_filename=os.path.basename(board_path)
        board_filename_noex=os.path.splitext(board_filename)[0]
        project_folder=os.path.dirname(board_path)
        timelapse_folder=board_filename_noex+'-timelapse'
        timelapse_folder_path=os.path.join(project_folder, timelapse_folder)
        if not os.path.exists(timelapse_folder_path):
            print('Timelapse folder does not exist. creating one now')
            os.mkdir(timelapse_folder_path)
            print('Timelapse folder created')

        timelapse_files=os.listdir(timelapse_folder_path)
        timelapse_number=extract_biggest_number(timelapse_files)
        pc = pcbnew.PLOT_CONTROLLER(self.board)
        po = pc.GetPlotOptions()
        po.SetOutputDirectory(timelapse_folder_path)
        po.SetPlotFrameRef(False)
        po.SetLineWidth(pcbnew.FromMM(0.35))
        po.SetScale(1)
        po.SetUseAuxOrigin(True)
        po.SetMirror(False)
        po.SetExcludeEdgeLayer(True)
        # Set current layer

        # Plot single layer to file

        timelapse_number += 1
        processed_svg_files = []
        for layer in layers:
            pc.SetLayer(layer['layer'])
            layer['layer']
            pc.OpenPlotfile('-'+layer['name']+'-'+str(timelapse_number).zfill(4), pcbnew.PLOT_FORMAT_SVG, layer['name'])
            pc.PlotLayer()
            pc.ClosePlot()
            output_filename = pc.GetPlotFileName()
            processor = SvgProcessor(output_filename)
            def colorize(original):
                if original.lower() == '#000000':
                    return layer['color']
                return original
            processor.apply_color_transform(colorize)
            processor.wrap_with_group({
                'opacity': str(layer['alpha']),
            })

            output_filename2 = os.path.join(timelapse_folder_path, 'processed-' + os.path.basename(output_filename))
            processor.write(output_filename2)
            processed_svg_files.append((output_filename2, processor))
            os.remove(output_filename)

        final_svg = os.path.join(timelapse_folder_path, board_filename_noex+'-'+str(timelapse_number).zfill(4)+'.svg')
        shutil.copyfile(processed_svg_files[0][0], final_svg)
        output_processor = SvgProcessor(final_svg)
        for processed_svg_file, processor in processed_svg_files:
            output_processor.import_groups(processor)
            os.remove(processed_svg_file)
        output_processor.set_title(board_filename_noex)
        output_processor.write(final_svg)

        # Remove the exported file if there were no new changes
        if timelapse_number != 1:
            with open(os.path.join(timelapse_folder_path, board_filename_noex+'-'+str(timelapse_number - 1).zfill(4)+'.svg')) as old_file:
                with open(final_svg) as new_file:
                    if old_file.read() == new_file.read():
                        timelapse_number -= 1
                        os.remove(final_svg)

        return True


    def Run(self):
        self.rt = RepeatedTimer(capture_interval, self.screenshot)

print("Registered to pcbnew") 
SimplePlugin().register() # Instantiate and register to Pcbnew
