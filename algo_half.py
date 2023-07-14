class Activity:
    def __init__(self, name, location, size):
        self.name = name
        self.location = location
        self.size = size
    
    def __eq__(self, other):
        if isinstance(other, Activity):
            return all(getattr(self, attr) == getattr(other, attr) for attr in vars(self))
        return False

class Group:
    def __init__(self, name, location, size):
        self.name = name
        self.location = location
        self.size = size
    
    def __eq__(self, other):
        if isinstance(other, Group):
            return all(getattr(self, attr) == getattr(other, attr) for attr in vars(self))
        return False

class Bus:
    def __init__(self, name, size, license = "B", constraints = []):
        self.name = name
        self.size = size
        self.license = license
        self.constraints = constraints

    def __eq__(self, other):
        if isinstance(other, Bus):
            return all(getattr(self, attr) == getattr(other, attr) for attr in vars(self))
        return False

    def __hash__(self):
        attrs = vars(self).copy()
        attrs['constraints'] = tuple(attrs['constraints'])
        sorted_attrs = sorted(attrs.items())
        return hash(tuple(sorted_attrs))

class Staff:
    def __init__(self, name, group, activity, full = False, license = "B"):
        self.name = name
        self.group = group
        self.activity = activity
        self.full = full
        self.license = license

    def __eq__(self, other):
        if isinstance(other, Staff):
            return all(getattr(self, attr) == getattr(other, attr) for attr in vars(self))
        return False

class Planning:
    def __init__(self, activity, group, staffs, time, schedule = "", buses = [], drivers = [], size = 0, s_size = ""):
        self.activity = activity
        self.group = group
        self.staffs = staffs
        self.time = time
        self.schedule = schedule
        self.buses = buses 
        self.drivers = drivers 
        self.size = size 
        self.s_size = s_size

    def __eq__(self, other):
        if isinstance(other, Planning):
            return all(getattr(self, attr) == getattr(other, attr) for attr in vars(self))
        return False

#time = "dd/mm/DDDD/t" ex : "15/06/2023/m", m = morning, a = afternoon, f = fullday
#return plan halfday + les vehicules indispo si qql part la journée 

morning_begin = "8h30"
afternoon_begin = "13h30"

def any_full(p):
    return any(s.full for s in p.staffs)

def m_bus(p, bus_list, m, spe_buses = []):
    bus_no_c = [bu for bu in bus_list if bu.constraints == [] and bu not in spe_buses] #enlever SPE BUS ici
    bus_with_c = [bu for bu in bus_list if any(p.activity.name.strip()[:3].lower() == c for c in bu.constraints) and bu not in spe_buses]
    bu = m(bus_no_c, key=lambda x: x.size)
    if bus_with_c != []:
        bc = m(bus_with_c, key=lambda x: x.size)
        if m(bu.size,bc.size) == bc.size:
            bu = bc
    return bu

def opti_bus(p, bus_list, eff, spe_buses = []):
    bus_no_c = [bu for bu in bus_list if bu.constraints == [] and bu not in spe_buses] #enlever SPE BUS ici
    bus_with_c = [bu for bu in bus_list if any(p.activity.name.strip()[:3].lower() == c for c in bu.constraints) and bu not in spe_buses]
    bu = find_bus(bus_no_c, eff)
    if bus_with_c:
        bc = find_bus(bus_with_c, eff)
        return find_bus([bc,bu], eff)
    return bu

def find_bus(buses, n):
    buses_greater_than_n = [bus for bus in buses if bus.size >= n]
    if buses_greater_than_n:
        min_size_bus = min(buses_greater_than_n, key=lambda bus: bus.size)
        return min_size_bus
    else:
        max_size_bus = max(buses, key=lambda bus: bus.size)
        return max_size_bus

def planning_halfday(staff_list, bs_list, s_drivers, time): #prendre en compte dans les passagers les autres moniteurs
    plans_list = []
    b_list = bs_list.copy()
    bus_list = b_list.copy()
    special_drivers = s_drivers.copy()

    for s in staff_list:
        check = [p for p in plans_list if p.group == s.group and p.activity == s.activity]
        if check != []:
            i = plans_list.index(check[0])
            plans_list[i].staffs.append(s)
            plans_list[i].size += s.activity.size
            if plans_list[i].size >= eval(s.group.size):
                plans_list[i].size = eval(s.group.size)
                plans_list[i].s_size = s.group.size
        else:
            time_tmp = time
            schedule = morning_begin
            if time[11] == "a":
                schedule = afternoon_begin
            if s.full:
                #time_tmp[11] = "f"
                pass
            # if accro alors size = group size
            plans_list.append(Planning(s.activity, s.group, [s], time_tmp, schedule, size = s.activity.size))
    
    plans_list.sort(key=lambda p: p.size, reverse=True)

    try:
        for p in plans_list:
                eff = p.size + len(p.staffs)-1 #possibilité d'améliorer, car cela suppose que seul un moniteur conduit
                p.drivers = [] #this two lines are here for avoiding python copy adress mechanism
                p.buses = []

                if p.group.location == p.activity.location: #no traj
                    check_same = [pl for pl in plans_list if pl.group.location == pl.activity.location == p.group.location and pl.buses != []]
                    if check_same != []:
                        p.buses.append(check_same[0].buses[0])
                        p.drivers.append("BE")
                    else:
                        b = m_bus(p, bus_list, min, [bu for bu in bus_list if bu.license == "E"])
                        p.buses.append(b)
                        bus_list.remove(b)         
                        p.drivers.append("BE")
                        if any_full(p):
                            b_list.remove(b)
                else:
                    spe_buses = [b for b in bus_list if b.license == "E"]
                    spe_buses.sort(key=lambda b: b.size, reverse=True)
                    n = len(special_drivers)
                    buses = []

                    for b in spe_buses:
                        if (eff//b.size > 0 or abs(b.size - eff) <= max([bs.size for bs in bus_list if bs not in spe_buses and (bs.constraints == [] or any(p.activity.name.strip()[:3].lower() == c for c in bs.constraints)) ]) ) and n > 0 and spe_buses != []:
                            eff -= b.size
                            bu = opti_bus(p, bus_list, eff, spe_buses)
                            if any_full(p):
                                b_list.remove(b)    
                            p.drivers.append(special_drivers[0])
                            special_drivers.remove(special_drivers[0])
                            buses.append(b)
                            bus_list.remove(b) 
                            n-=1        
                            if eff-bu.size <=0:
                                eff -= bu.size
                                buses.append(bu)
                                p.drivers.append("BE")
                                bus_list.remove(bu)
                                if any_full(p):
                                    b_list.remove(bu)
                                break
                    p.buses = buses
                    if eff <= 0:
                        pass
                    else:
                        while eff > 0:
                            b = opti_bus(p, bus_list, eff, spe_buses) #improve the handling whe the is no more bus left
                            eff -= b.size
                            p.buses.append(b)
                            if not any(d == "BE" for d in p.drivers):
                                p.drivers.append("BE")
                            bus_list.remove(b)
                            if any_full(p):
                                b_list.remove(b)
    except ValueError:
        print("No more bus")

    return plans_list, b_list

activity_size = {"escalade" : 10, "via corda" : 10, "canyoning" : 10, "speleo" : 10, "canoe" : 15}
