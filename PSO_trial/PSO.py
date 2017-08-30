import numpy as np
import random
from matplotlib import pyplot as plt
from matplotlib import animation, cm

#----------COST FUNCTION-----------#

#funcion to minimise, in this case a Rastrigin function (min at (0,0,0...))

def f(x):
    total = 0
    for i in range(len(x)):
        total += x[i]**2 - 10*np.cos(2*np.pi*x[i])
    total += 10*len(x)
    return total
    
#----------PARTICLE CLASS----------#

class Particle:
    def __init__(self, x0):
        self.position_i = []        #particle position
        self.velocity_i = []        #particle velocity
        self.pos_best_i = []        #particle's best position
        self.fit_i = -1            #particle fit ------------- ?
        self.fit_best_i = -1        #particle best fit
        
        self.pos_history = []       #position for animation
        
        #initialise particle's initial position and velocity
        for i in range(0, num_dimensions):
            self.velocity_i.append(random.uniform(-1,1))
            self.position_i.append(random.uniform(-5, 5)) 
            
    #find particle's current fit
    def evaluate(self, costFunc):
        self.fit_i = costFunc(self.position_i) 
        
        # check is this is a personal best
        if self.fit_i < self.fit_best_i or self.fit_best_i == -1:
            self.pos_best_i = self.position_i
            self.fit_best_i = self.fit_i
            
    # update new velocity
    def update_velocity(self, pos_best_g):
        w = .5                      #inertia constant
        c1 = 2.0                    #cognitive parameter
        c2 = 2.0                    #social parameter
        
        for i in range(0, num_dimensions):
            r1 = random.random()
            r2 = random.random()
            
            velocity_cognitive = c1 * r1 * (self.pos_best_i[i] - self.position_i[i])
            velocity_social = c2 * r2 * (pos_best_g[i] - self.position_i[i])
            self.velocity_i[i] = w*self.velocity_i[i] + velocity_cognitive + velocity_social
    
    # update new position using new velocity
    def update_position(self, bounds):
        
        for i in range(0,num_dimensions):
            self.position_i[i]= self.position_i[i] + self.velocity_i[i]
            
            #adjust if particle goes above max bound
            if self.position_i[i] > bounds[i][1]:
                self.position_i[i] = bounds[i][1]
                
            #adjust if particle goes below min bound
            if self.position_i[i] < bounds[i][0]:
                self.position_i[i] = bounds[i][0]
                
                
    def position_history_append(self, x, num_dimensions):
        self.pos_history.append(x)
        #print self.pos_history


#-------------PSO CLASS--------------#

class PSO:
    
    def __init__(self, costFunc, bounds, num_particles, maxiter):
        global num_dimensions
        
        num_dimensions = len(bounds)
        fit_best_g = -1             #best swarm fit
        pos_best_g = []             #best swarm position
        
        #initialise the swarm
        swarm = []
        for i in range(0, num_particles):
            swarm.append(Particle(bounds))
            
        #begin optimisation 
        i = 0
        
        while i < maxiter:
            print swarm
            #calculate fit for swarm
            for j in range(0, num_particles):
                swarm[j].evaluate(costFunc)
                
                #determine if current particle is best globally
                if swarm[j].fit_i < fit_best_g or fit_best_g == -1:
                    pos_best_g = list(swarm[j].position_i)
                    fit_best_g = float(swarm[j].fit_i)
                
            # update all velocites and positions   
            for j in range(0,num_particles):
                swarm[j].position_history_append(swarm[j].position_i, num_dimensions)
                #print swarm[j].pos_history
                swarm[j].update_velocity(pos_best_g)
                swarm[j].update_position(bounds)                
            i += 1
        
        def get_coords(x, coord, particle_num, iteration_num):
            coordinate = []
            for i in range(0,maxiter):
                coordinate.append(x[particle_num][i][coord])
            #print coordinate
            return coordinate[iteration_num]
        
             
        # def update_plot(k, fig):
        #     for i in range(0, num_particles):
        #         x1 = get_coords(loc, 0, i, k)
        #         x2 = get_coords(loc, 1, i, k)   
        #         plt.plot(x1, x2, 'ro', ms=3)
                   
        loc = []
        for j in range(0, num_particles):
           loc.append(swarm[j].pos_history)
       
        
        
        #print final results
        print 'FINAL:'
        print pos_best_g
        print fit_best_g
        
        #plot function and solution
        x = np.arange(-5,5,0.1)
        y = np.arange(-5,5,0.1)
        X,Y = np.meshgrid(x,y)
        Z = f([X,Y])       
        plt.figure()
        plt.xlabel('x')
        plt.ylabel('y')
        plt.contour(X,Y,Z, 8)
        for i in range(0, num_particles):
            x1 = get_coords(loc, 0, i, 0)
            x2 = get_coords(loc, 1, i, 0)
            plt.plot(x1, x2, 'go', ms=5)
        #plt.plot(pos_best_g[0], pos_best_g[1], 'ro', ms=3)
        plt.show()
                        
    
#-------------RUN---------------#

bounds=[(-5,5),(-5,5)]                          # input bounds [(x1_min,x1_max),(x2_min,x2_max)...]
PSO(f,bounds,num_particles=30,maxiter=15)
