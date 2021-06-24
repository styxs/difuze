import xml.etree.ElementTree as ET
from xml.dom import minidom
import sys
import re
import platform
from copy import copy

HYPERCALL_IDS = {
    'do_set_trap_table':        0,
    'do_mmu_update':            1,
    'do_set_gdt':               2,
    'do_stack_switch':          3,
    'do_set_callbacks':         4,
    'do_fpu_taskswitch':        5,
    'do_sched_op_compat':       6,
    'do_platform_op':           7,
    'do_set_debugreg':          8,
    'do_get_debugreg':          9,
    'do_update_descriptor':    10,
    'do_memory_op':            12,
    'do_multicall':            13,
    'do_update_va_mapping':    14,
    'do_set_timer_op':         15,
    'do_event_channel_op_compat': 16,
    'do_xen_version':          17,
    'do_console_io':           18,
    'do_physdev_op_compat':    19,
    'do_grant_table_op':       20,
    'do_vm_assist':            21,
    'do_update_va_mapping_otherdomain': 22,
    'do_iret':                 23,
    'do_vcpu_op':              24,
    'do_set_segment_base':     25,
    'do_mmuext_op':            26,
    'do_xsm_op':               27,
    'do_nmi_op':               28,
    'do_sched_op':             29,
    'do_callback_op':          30,
    'do_xenoprof_op':          31,
    'do_event_channel_op':     32,
    'do_physdev_op':           33,
    'do_hvm_op':               34,
    'do_sysctl':               35,
    'do_domctl':               36,
    'do_kexec_op':             37,
    'do_tmem_op':              38,
    'do_argo_op':              39,
    'do_xenpmu_op':            40,
    'do_dm_op':                41,
    'do_hypfs_op':             42,
}

# TODO: ENUMS do not carry value information in the xml generated by c2xml
# TODO: uint8_t's are being interpreted as strings atm
# TODO: unions

fname = sys.argv[1]
devname = sys.argv[2]
#print("Fname is:", fname)
ioctl_id = sys.argv[3]
main_struct = sys.argv[4]
hypercall_id = HYPERCALL_IDS[sys.argv[5]]
tree = ET.parse(fname)

root = tree.getroot()
skip_len = len('<?xml version="1.0" ?>')
struct_list = []
seen = []

def prettify(elem):
	#Return a pretty-printed XML string for the Element.
	rough_string = ET.tostring(elem, 'utf-8')
	reparsed = minidom.parseString(rough_string)
	return reparsed.toprettyxml(indent="	")[skip_len+1:-1:]


def union_hero(choice_block, required_structs, parent_struct_name):
	for choice in choice_block:
		pointers = choice.findall('Pointer')
		for ptr in pointers:
			ptr_to = ptr.get('ptr_to')
			if ptr_to is not None:
				if ptr_to in ['Number', 'String', 'function']:
					pass

				else:
					resolved_ele = root[lookup.get(ptr_to)]
					if resolved_ele in required_structs:
						required_structs.remove(resolved_ele)
					required_structs.append(resolved_ele)
					# if it's a recursive struct, don't recruse into it
					if parent_struct_name != ptr_to:
						# TODO: CHECKME
						doit(resolved_ele, required_structs)
		
		blocks = choice.findall('Block')
		for block in blocks:
			# if the block is a ref, we need to define that struct
			# though we won't need a blob for it
			# we'll also want to recurse into it to check for ptrs
			ref_to = block.get('ref')
			if ref_to is not None:
				resolved_ele = root[lookup.get(ref_to)]
				# note, we'll want a struct def for this, but not a blob since it's part of the struct
				if resolved_ele in required_structs:
					required_structs.remove(resolved_ele)
				required_structs.append(resolved_ele)
				doit(resolved_ele, required_structs)

			# if it's an array...ugh
			occurs = block.get('maxOccurs')
			if occurs is not None:
				array_hero(block, required_structs, parent_struct_name, occurs)


def array_hero(block, required_structs, parent_struct_name, occurs):
	elem_size_bytes = int(block.get('elem_size'))
	arr_offset = int(block.get('offset'))
	pointers = block.findall('Pointer')
	for ptr in pointers:
		ptr_to = ptr.get('ptr_to')
		if ptr_to is not None:
			# generic ptr arry
			if ptr_to in ['Number', 'String', 'function']:
				pass

			# complex ptr array
			else:
				resolved_ele = root[lookup.get(ptr_to)]
				if resolved_ele in required_structs:
					required_structs.remove(resolved_ele)
				required_structs.append(resolved_ele)
				# if it's a recursive struct, don't recurse into it
				if parent_struct_name != ptr_to:
					# TODO: CHECKME
					# reset cur_offset to 0 because it's a pointer
					doit(resolved_ele, required_structs)


	inner_blocks = block.findall('Block')
	for inner_block in inner_blocks:
		ref_to = inner_block.get('ref')
		if ref_to is not None:
			resolved_ele = root[lookup.get(ref_to)]
			if resolved_ele in required_structs:
				required_structs.remove(resolved_ele)
			required_structs.append(resolved_ele)
			doit(resolved_ele, required_structs)
		
		# if it's an array...ugh
		inner_occurs = inner_block.get('maxOccurs')
		if inner_occurs is not None:
			new_occurs = str(int(occurs) * int(inner_occurs))
			array_hero(inner_block, required_structs, parent_struct_name, new_occurs)


	# jay CHECKME. FUCK.
	choices = block.findall('Choice')
	for choice in choices:
		union_hero(choice, required_structs, parent_struct_name)


def doit(node, required_structs):
	struct_name = node.get('name')
	pointers = node.findall('Pointer')

	for ptr in pointers:
		ptr_to = ptr.get('ptr_to')
		if ptr_to is not None:
			if ptr_to in ['Number', 'String', 'function']:
				pass

			else:
				resolved_ele = root[lookup.get(ptr_to)]
				if resolved_ele in required_structs:
					required_structs.remove(resolved_ele)
				required_structs.append(resolved_ele)
				# if it's a recursive struct, don't recurse into it
				if struct_name != ptr_to and ptr_to not in seen:
					seen.append(ptr_to)
					doit(resolved_ele, required_structs)
	
	blocks = node.findall('Block')
	for block in blocks:
		# if the block is a ref, we need to define that struct
		# though we won't need a blob for it
		# we'll also want to recurse into it to check for ptrs
		ref_to = block.get('ref')
		if ref_to is not None:
			resolved_ele = root[lookup.get(ref_to)]
			if resolved_ele in required_structs:
				required_structs.remove(resolved_ele)
			required_structs.append(resolved_ele)
			# Also note, this struct ref may have ptrs in it, so pass along our new offset
			doit(resolved_ele, required_structs)

		# if it's an array...ugh
		occurs = block.get('maxOccurs')
		if occurs is not None:
			array_hero(block, required_structs, struct_name, occurs)

	choices = node.findall('Choice')
	for choice in choices:
		# note this choice may have ptrs, so pass along our current offset
		union_hero(choice, required_structs, struct_name)
	
	return required_structs

def create_lookup(root):
	lookup = {}
	for x in range(len(root)):
		lookup[root[x].get('name')] = x

	return lookup


def create_info(devname, hypercall_id, ioctl_id, target_struct):
	info_node = ET.Element('Config')
	devname_node = ET.Element('devname', value=devname)
	info_node.append(devname_node)
	hypercall_id_node = ET.Element('hypercall_id', value=str(hypercall_id))
	info_node.append(hypercall_id_node)
	ioctl_id_node = ET.Element('ioctl_id', value=ioctl_id)
	info_node.append(ioctl_id_node)
	target_struct_node = ET.Element('target_struct', value=target_struct)
	info_node.append(target_struct_node)

	info_node.tail='\n'
	return info_node

def create_pit(dm_nodes, info_node):
	# create the outermost node
	peach_node = ET.Element('Mango', version='1.0', author='jay` bot', description="kickass autogenerated jpit")

	# info node next
	peach_node.append(info_node)

	# next we'll output the data models
	covered = []
	dm_nodes.reverse()
	for dm in dm_nodes:
		if dm not in covered:
			peach_node.append(dm)
			covered.append(dm)
		else:
			print "WTF. Repeat DM!!"
			import ipdb;ipdb.set_trace()
			import sys;sys.exit(1)

	print prettify(peach_node)

def make_nice(dm):
	if type(dm) != list:
		if dm.tag != 'DataModel':
			dm.text = ''
			dm.tail = ''
		else:
			dm.text = ''
	for field in dm:
		field.text = ''
		field.tail = ''
		children = field.getchildren()
		for child in children:
			make_nice(child)

lookup = create_lookup(root)
start_struct = root[lookup.get(main_struct)]
required_structs = []
required_structs.append(start_struct)
ok = doit(start_struct, required_structs)
info_node = create_info(devname, hypercall_id, ioctl_id, main_struct)

for dm in required_structs:
	make_nice(dm)
create_pit(required_structs, info_node)
