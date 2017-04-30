import numpy as np
import os
import nibabel as nib
from os.path import join as jph

from sympy.core.cache import clear_cache


def indian_file_parser(s, sh=None):
    """
    An indian file is a string whose shape needs to be changed, in function of its content and an optional parameter sh
    that defines the shape of the output.
    This function transform the indian file in a data structure,
    according to the information that can be parsed in the file:
    A - list of vectors transformed into a np.ndarray.
    B - list of numbers, transformed into a np.ndarray, or single number stored as a single float.
    C - list of strings separated by <>.
    D - everything else becomes a string.

    :param s: string indian file
    :param sh: shape related
    :return: parsed indian file of adequate output.
    """

    s = s.strip()  # removes initial and final spaces.

    if ('(' in s) and (')' in s):  # A
        s = s[1:-1]  # removes initial and final ( )
        a = ['(' + v + ')' for v in s.split(') (')]
    elif s.replace('-', '').replace('.', '').replace(' ', '').replace('e', '').isdigit():  # B
        if ' ' in s:
            a = np.array([float(x) for x in s.split()])
            if sh is not None:
                a = a.reshape(sh)
        else:
            a = float(s)
    elif ('<' in s) and ('>' in s):  # C
        s = s[1:-1]  # removes initial and final < >
        a = [v for v in s.split('> <')]
    else:  # D
        a = s[:]

    # added to work with ParaVision 6:
    if isinstance(a, list):
        if len(a) == 1:
            a = a[0]

    return a


def var_name_clean(line_in):
    """
    Removes #, $ and PVM_ from line_in
    :param line_in: input string
    :return: output string cleaned from #, $ and PVM_
    """
    line_out = line_in.replace('#', '').replace('$', '').replace('PVM_', '').strip()
    return line_out


def bruker_read_files(param_file, data_path, sub_scan_num='1'):
    """
    Reads parameters files of from Bruckert raw data imaging format.
    It parses the files 'acqp' 'method' and 'reco'
    :param param_file: file parameter.
    :param data_path: path to data.
    :param sub_scan_num: number of the sub-scan folder where reco and visu_pars is stored.
    :return: dict_info dictionary with the parsed informations from the input file.
    """
    # reco is only present for the sub_scan number '1'.
    # There is an visu_pars for each sub-scan.
    if param_file.lower() == 'reco':
        if os.path.exists(jph(data_path, 'pdata', '1', 'reco')):
            f = open(jph(data_path, 'pdata', '1', 'reco'), 'r')
        else:
            print('File {} does not exists'.format(jph(data_path, 'pdata', '1', 'reco')))
            return {}
    elif param_file.lower() == 'acqp':
        if os.path.exists(jph(data_path, 'acqp')):
            f = open(jph(data_path, 'acqp'), 'r')
        else:
            print('File {} does not exists'.format(jph(data_path, 'acqp')))
            return {}
    elif param_file.lower() == 'method':
        if os.path.exists(jph(data_path, 'method')):
            f = open(jph(data_path, 'method'), 'r')
        else:
            print('File {} does not exists'.format(jph(data_path, 'method')))
            return {}
    elif param_file.lower() == 'visu_pars':
        if os.path.exists(jph(data_path, 'pdata', str(sub_scan_num), 'visu_pars')):
            f = open(jph(data_path, 'pdata', str(sub_scan_num), 'visu_pars'), 'r')
        else:
            print('File {} does not exists'.format(jph(data_path, 'pdata', str(sub_scan_num), 'visu_pars')))
            return {}
    elif param_file.lower() == 'subject':
        if os.path.exists(jph(data_path, 'subject')):
            f = open(jph(data_path, 'subject'), 'r')
        else:
            print('File {} does not exists'.format(jph(data_path, 'subject')))
            return {}
    else:
        raise IOError("param_file input must be the string 'reco', 'acqp', 'method', 'visu_pars' or 'subject'")

    dict_info = {}
    lines = f.readlines()

    for line_num in range(len(lines)):
        '''
        Relevant information are in the lines with '##'.
        A: for the parameters that have arrays values specified between (), with values in the next line.
           Values in the next line can be parsed in lists or np.ndarray, if they contains also characters
           or only numbers.
        '''

        line_in = lines[line_num]

        # if line_num == 671 and param_file.lower() == 'visu_pars':
        #     print 'spam'

        if '##' in line_in:

            # A:
            if ('$' in line_in) and ('(' in line_in) and ('<' not in line_in):

                splitted_line = line_in.split('=')
                # name of the variable contained in the row, and shape:
                var_name = var_name_clean(splitted_line[0][3:])

                done = False
                indian_file = ''
                pos = line_num
                sh = splitted_line[1]
                # this is not the shape of the vector but the beginning of a full vector.
                if sh.replace(' ', '').endswith(',\n'):
                    sh = sh.replace('(', '').replace(')', '').replace('\n', '').strip()
                    indian_file += sh
                    sh = None
                # this is not the shape of the vector but a full vector.
                elif sh.replace(' ', '').endswith(')\n') and '.' in sh:
                    sh = sh.replace('(', '').replace(')', '').replace('\n', '').strip()
                    indian_file += sh
                    sh = None
                # this is finally the shape of the vector that will start in the next line.
                else:
                    sh = sh.replace('(', '').replace(')', '').replace('\n', '').strip()
                    sh = [int(num) for num in sh.split(',')]

                while not done:

                    pos += 1
                    # collect the indian file: info related to the same variables that can appears on multiple rows.
                    line_to_explore = lines[pos]  # tell seek does not work in the line iterators...

                    if ('##' in line_to_explore) or ('$$' in line_to_explore):
                        # indian file is over
                        done = True

                    else:
                        # we store the rows in the indian file all in the same string.
                        indian_file += line_to_explore.replace('\n', '').strip() + ' '

                dict_info[var_name] = indian_file_parser(indian_file, sh)

            # B:
            elif ('$' in line_in) and ('(' not in line_in):
                splitted_line = line_in.split('=')
                var_name = var_name_clean(splitted_line[0][3:])
                indian_file = splitted_line[1]

                dict_info[var_name] = indian_file_parser(indian_file)

            # C:
            elif ('$' not in line_in) and ('(' in line_in):

                splitted_line = line_in.split('=')
                var_name = var_name_clean(splitted_line[0][2:])

                done = False
                indian_file = splitted_line[1].strip() + ' '
                pos = line_num

                while not done:

                    pos += 1

                    # collect the indian file: info related to the same variables that can appears on multiple rows.
                    line_to_explore = lines[pos]  # tell seek does not work in the line iterators...

                    if ('##' in line_to_explore) or ('$$' in line_to_explore):
                        # indian file is over
                        done = True

                    else:
                        # we store the rows in the indian file all in the same string.
                        indian_file += line_to_explore.replace('\n', '').strip() + ' '

                dict_info[var_name] = indian_file_parser(indian_file)

            # D:
            elif ('$' not in line_in) and ('(' not in line_in):
                splitted_line = line_in.split('=')
                var_name = var_name_clean(splitted_line[0])
                indian_file = splitted_line[1].replace('=', '').strip()
                dict_info[var_name] = indian_file_parser(indian_file)
            # General case: take it as a simple string.
            else:
                splitted_line = line_in.split('=')
                var_name = var_name_clean(splitted_line[0])
                dict_info[var_name] = splitted_line[1].replace('(', '').replace(')', '').replace('\n', ''). \
                                                       replace('<', '').replace('>', '').replace(',', ' ').strip()

        else:
            # line does not contain any assignable variable, so this information is not included in the info.
            pass

    clear_cache()
    return dict_info


def normalise_b_vect(b_vect, remove_nan=True):

    b_vect_normalised = np.zeros_like(b_vect)
    norms = np.linalg.norm(b_vect, axis=1)

    for r in range(b_vect.shape[0]):
        if norms[r] < 10e-5:
            b_vect_normalised[r, :] = np.nan
        else:
            b_vect_normalised[r, :] = (1 / float(norms[r])) * b_vect[r, :]

    if remove_nan:
        b_vect_normalised = np.nan_to_num(b_vect_normalised)

    return b_vect_normalised


def slope_corrector(data, slope, num_initial_dir_to_skip=None):

    if len(data.shape) > 5:
        raise IOError('4d or lower dimensional images allowed. Input data has shape'.format(data.shape))

    data = data.astype(np.float64)

    if num_initial_dir_to_skip is not None:
        slope = slope[num_initial_dir_to_skip:]
        data = data[..., num_initial_dir_to_skip:]

    if isinstance(slope, int) or isinstance(slope, float):
        # scalar times 3d array
        data = slope * data

    elif len(data.shape) == 3 and len(slope.shape) == 1:
        # each slice of the 3d image is multiplied an element of the slope
        if data.shape[2] == slope.shape[0]:
            for t, sl in enumerate(slope):
                data[..., t] = data[..., t] * sl
        else:
            raise IOError('Shape of the 2d image and slope dimensions are not consistent')

    elif len(data.shape) == 4 and len(slope.shape) == 1 and data.shape[2] == slope.shape[0]:

        if slope.size == data.shape[2]:
            for k in range(data.shape[3]):
                for t in range(slope.size):
                    data[..., t, k] = data[..., t, k] * slope[t]
        else:
            raise IOError('Spam, consider your case debugging from here.')

    elif len(data.shape) == 5 and len(slope.shape) == 1 and data.shape[3] == slope.shape[0]:

        if slope.size == data.shape[3]:
            for k in range(data.shape[4]):
                for t in range(slope.size):
                    data[..., t, k] = data[..., t, k] * slope[t]
        else:
            raise IOError('Spam, consider your case debugging from here.')

    else:
        if slope.size == data.shape[3]:
            for t in range(data.shape[3]):
                data[..., t] = data[..., t] * slope[t]
        else:
            raise IOError('Shape of the 3d image and slope dimensions are not consistent')

    return data


def compute_affine(visu_core_orientation, method_slice_orient, method_spack_read_orient, method_method,
                   resolution, translation):
    """
    Converts the relevant (or supposed so) information from the Bruker files into the affine transformation
    of the nifti image.
    ---
    Information that are believed to be relevant are:
     visu_pars['VisuCoreOrientation'] -> visu_core_orientation  (not used yet but believed to be relevant)
     method['SPackArrSliceOrient']    -> method_slice_orient
     method['SPackArrReadOrient']    -> method_spack_read_orient
     method['Method']                 -> method_method       (not used yet but may be relevant for debub)
     visu_pars['VisuCorePosition']    -> translations
     list(method['SpatResol']         ->  resolution  (+ acqp['ACQ_slice_thick'] if 2D)
    ---
    :param visu_core_orientation: 9x1 matrix
    :param method_slice_orient: can be 'axial' 'sagittal' 'coronal'
    :param method_method: acquisition modality as ''RARE' or 'DtiEpi' or 'MSME'
    :param resolution: 3x1 matrix
    :param translation: 3x1 matrix
    :return:
    """
    # Not yet clear how to use visu_core_orientation and method_slice_orient to obtain the orientation matrix in
    # a consistent way. Based on empirical experiments for the moment.
    # TODO orientation requires further examination and proper testing before cleaning up this part of the code.

    # nifti is voxel to world. Is VisuCoreOrientation world to voxel? Seems yes.
    visu_core_orientation = np.linalg.inv(visu_core_orientation).astype(np.float64)

    # tables below are based on empirical evaluations - (visu_core_orientation not used in this version).
    invert_ap = False
    if method_spack_read_orient == 'A_P':
        invert_ap = True

    if invert_ap:
        slice_orient_map = {'axial':    np.array([[-1, 0, 0], [0, 0, 1], [0, -1, 0]]),  # RSP
                            'sagittal': np.array([[0, 0, -1], [0, 1, 0], [-1, 0, 0]]),  # SPR
                            'coronal':  np.array([[-1, 0, 0], [0, 1, 0], [0, 0, 1]])}   # RPI
    else:
        slice_orient_map = {'axial'    : np.array([[-1, 0, 0], [0, 0, -1], [0, -1, 0]]),  # RSA
                            'sagittal' : np.array([[0, 0, -1], [0, -1, 0], [-1, 0, 0]]),  # SAR
                            'coronal'  : np.array([[-1, 0, 0], [0, -1, 0], [0, 0, 1]])}   # RAI

    if method_slice_orient not in slice_orient_map.keys():
        raise IOError("Double check the attribute method['SPackArrSliceOrient'].")

    result = np.eye(4)
    # rotational part - multiply directions on the left
    result[0:3, 0:3] = slice_orient_map[method_slice_orient].dot(np.diag(resolution))
    # translational part
    result[0:3, 3] = translation

    # sanity check
    if invert_ap:
        assert abs(np.linalg.det(result) + np.prod(resolution)) < 10e-7
    else:
        assert abs(np.linalg.det(result) - np.prod(resolution)) < 10e-7

    return result


def from_dict_to_txt_sorted(dict_input, pfi_output):
    """
    Save the information contained in a dictionary into a txt file at the specified path.
    :param dict_input: input structure dictionary
    :param pfi_output: path to file.
    :return:
    """
    sorted_keys = sorted(dict_input.keys())

    with open(pfi_output, 'w') as f:
        f.writelines('{0} = {1} \n'.format(k, dict_input[k]) for k in sorted_keys)


def set_new_data(image, new_data, new_dtype=None, remove_nan=True):
    """
    From a nibabel image and a numpy array it creates a new image with
    the same header of the image and the new_data as its data.
    :param image: nibabel image
    :param new_data: numpy array
    :param new_dtype:
    :param remove_nan:
    :return: nibabel image
    """
    if remove_nan:
        new_data = np.nan_to_num(new_data)

    # if nifty1
    if image.header['sizeof_hdr'] == 348:
        new_image = nib.Nifti1Image(new_data, image.affine, header=image.header)
    # if nifty2
    elif image.header['sizeof_hdr'] == 540:
        new_image = nib.Nifti2Image(new_data, image.affine, header=image.header)
    else:
        raise IOError('Input image header problem')

    # update data type:
    if new_dtype is None:
        new_image.set_data_dtype(new_data.dtype)
    else:
        new_image.set_data_dtype(new_dtype)

    return new_image
