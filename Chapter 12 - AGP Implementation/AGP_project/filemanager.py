# -*- coding: utf-8 -*-
from os import path
class DataSaver:
    name = ""
    result = ""
    directory = None
    max_areas = None
    
    def __init__(self, tri_result, project, version=1, directory=None):
        self.name = project
        self.result = tri_result
        p_name = project + "_%d" % version
        if directory is not None:
            self.directory = path.join(directory, p_name)
        else:
            wd = path.curdir
            self.directory = path.join(wd, p_name)

    def _write(self, data, extension):
        fp = self.directory + extension
        #if not path.exists(fp):
            
        with open(fp, "w+") as f:
            f.write(data)
        
    def _node_file(self):
        """
        TODO add attribute support
        
        First line: <# of vertices> <dimension (must be 2)> <# of attributes> <# of boundary markers (0 or 1)>
        Remaining lines: <vertex #> <x> <y> [attributes] [boundary marker] 
        """
        vertices = self.result["vertices"]
        markers = self.result["vertex_markers"]
        v_count = len(vertices)
        att_count = 0
        boundary = 1
        first_line = "%d  2  %d  %d" % (v_count, att_count, boundary)
        row_temp = "%d  %.3f  %.3f %d"
        file_lines = [first_line]
        for i in range(len(vertices)):
            vx, vy = vertices[i]
            v_mark = markers[i][0]
            file_lines.append(row_temp  % (i, vx, vy, v_mark))
        return "\n".join(file_lines)
                
    def _ele_file(self):
        """
        First line: <# of triangles> <nodes per triangle> <# of attributes>
        Remaining lines: <triangle #> <node> <node> <node> ... [attributes] 
        """
        tris = self.result["triangles"]
        t_count = len(tris)
        att_count = 0
        first_line = "%d  3  %d" % (t_count, att_count)
        row_temp = "%d %d %d %d"
        file_lines = [first_line]
        for i in range(len(tris)):
            n1, n2, n3 = tris[i]
            file_lines.append(row_temp  % (i, n1, n2, n3))
        return "\n".join(file_lines)
        
    def _area_file(self):
        """
        Save a .area file which maps triangles to area constraints
        parameters:
            area_map: index based off region and value is area
            
        File spec:
            First line: <# of triangles>
            Following lines: <triangle #> <maximum area>
        """
        first_line = "%d" % len(self.result["triangles"])
        file_lines = [first_line]
        for i in range(len(self.result["triangles"])):
            max_area = -1
            
            if "triangle_attributes" in self.result.keys():
                t_region = int(self.result["triangle_attributes"][i][0])
                if self.max_areas:
                    if t_region >= 0 and t_region < len(self.max_areas):
                        max_area = self.max_areas[t_region]
            file_lines.append("%d %.2f" % (i, max_area))
        return "\n".join(file_lines)
        

    def _poly_file(self, include_vertices=False):
        """
        First line: <# of vertices> <dimension (must be 2)> <# of attributes> <# of boundary markers (0 or 1)>
        Following lines: <vertex #> <x> <y> [attributes] [boundary marker]
        One line: <# of segments> <# of boundary markers (0 or 1)>
        Following lines: <segment #> <endpoint> <endpoint> [boundary marker]
        One line: <# of holes>
        Following lines: <hole #> <x> <y>
        Optional line: <# of regional attributes and/or area constraints>
        Optional following lines: <region #> <x> <y> <attribute> <maximum area>
        """
        if include_vertices:
            first_line = self._node_file()
        else:
            first_line = "0 2 0 0" # tells triangle there is a .node file
        file_lines = [first_line]
        if "segments" in self.result.keys():
            segs = self.result["segments"]
        else:
            segs = []
        if "segment_markers" in self.result.keys():
            seg_marks = self.result["segment_markers"]
            boundary_markers = 1
        else:
            seg_marks = []
            boundary_markers = 0
        seg_count = len(segs)
        seg_header = "%d  %d" % (seg_count, boundary_markers)
        file_lines.append(seg_header)
        for i in range(seg_count):
            ep1, ep2 = segs[i]
            mark = seg_marks[i]
            file_lines.append("%d  %d  %d  %d" % (i, ep1, ep2, mark))
        if "holes" in self.result.keys():
            holes = self.result["holes"]
            hole_count = len(holes)
            hole_header = "%d" % (hole_count)
            file_lines.append(hole_header)
            for i in range(hole_count):
                hx, hy = holes[i]
                file_lines.append("%d  %.3f  %.3f" % (i, hx, hy))
        else:
            file_lines.append("0") # zero holes
        if "regions" in self.result.keys():
            regs = self.result["regions"]
            reg_count = len(regs)
            reg_ats = 1
            file_lines.append("%d" % reg_ats) # region attribute count
            for i in range(reg_count):
                r = regs[i]
                rx = r[0]
                ry = r[1]
                ri = int(r[2])
                max_area = -1
                if self.max_areas:
                    if ri >= 0 and ri < len(self.max_areas):
                        max_area = self.max_areas[ri]
                rl = "%d  %.3f  %.3f  %.2f %.4f" % (i, rx, ry, ri, max_area)
                file_lines.append(rl)
        return "\n".join(file_lines)
        
    def set_region_areas(self, areas):
        # list of areas indexed on region id
        self.max_areas = areas
        
    def save_project(self):
        nf = self._node_file()
        self._write(nf, ".node")
        ef = self._ele_file()
        self._write(ef, ".ele")
        af = self._area_file()
        self._write(af, ".area")
        pf = self._poly_file()
        self._write(pf, ".poly")