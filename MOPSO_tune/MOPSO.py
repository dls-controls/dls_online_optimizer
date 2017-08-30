'''
Created on 7 Aug 2017

MOPSO program for benchmarking and parameter tuning.

@author: James Rogers
'''
from __future__ import division
import os
import math
import random
import time
import datetime
import Test_Functions

import pkg_resources
pkg_resources.require('scipy')
pkg_resources.require('numpy')
pkg_resources.require('matplotlib')
import numpy as np
from scipy import spatial

current_time_string = datetime.datetime.fromtimestamp(time.time()).strftime('%d.%m.%Y_%H.%M.%S')
store_location = '/dls/physics/students/qvi61384/MOPSO_tune/OUTPUT/Optimisation@{0}'.format(current_time_string)

if not os.path.exists('{0}/FRONTS'.format(store_location)):
    os.makedirs('{0}/FRONTS'.format(store_location))
    
pareto_front = []


class MOPSO:
    
    def __init__(self, swarm_size, functions, par_bounds, maxiter, inertia, cognitive_parameter, social_parameter):
        
        self.swarm_size = swarm_size
        self.functions = functions
        self.parameter_count = len(par_bounds)
        self.par_min = [item[0] for item in par_bounds]
        self.par_max = [item[1] for item in par_bounds]
        self.maxiter = maxiter
        self.inertia = inertia
        self.cognitive_parameter = cognitive_parameter
        self.social_parameter = social_parameter
    

    
    
    def evaluate_swarm(self, swarm):
        results = []
        for i in range(self.swarm_size):
            particle_result = self.functions(swarm[i].position_i)
            results.append(particle_result)
        return results
    

    
    def pareto_remover(self,a,b):
        """
        Function determines which of two points is the dominant in objective space.
        
        Args:
            a: list of objective values [obj1,obj2,...]
            b: list of objective values [obj1,obj2,...]
            
        Returns:
            Function will return the point that dominates the other. If neither dominates, return is False.
        """
        if all(a_i > b_i for (a_i,b_i) in zip(a,b)):         #does a dominate b?
            return a
        if all(a_i < b_i for (a_i,b_i) in zip(a,b)):         #does b dominate b?
            return b
        if all(a_i == b_i for (a_i,b_i) in zip(a,b)):        #are the points the same?
            return b
        else:
            return False
            
    def get_pareto_objectives(self, swarm):
        """
        Returns a list of objectives from front like list
        
        Args:
            swarm: list of solutions in the format (((param1,param2,...),(obj1,obj2,...),(err1,err2,...)),...).
            
        Returns:
            list of objectives in the format [(obj1,obj2,...),(obj1,obj2,...),...]
        """
        objectives = [particle[1] for particle in swarm]
        return objectives


    def pareto_test(self,a,b):
        """
        Determines whether a solution should remain in a pareto front.
        
        Args:
            a: list of objective values [obj1,obj2,...].
            b: list of objective values [obj1,obj2,...].
            
        Returns:
            False if a dominates b.
            True if both a and b are non-dominant.
        """
        if all(a_i > b_i for (a_i,b_i) in zip(a,b)):    #does a dominate b for all objectives?
            return False 
        else:
            return True
        
        
    def find_pareto_front(self,swarm):
        """
        For a given swarm of solutions, this function will determine the non-dominant set and update the pareto-front.
        
        Args:
            swarm: set of solutions in the form (((param1,param2,...),(obj1,obj2,...),(err1,err2,...)),...).
        
        Returns:
            None, but updates the global variable pareto_front with the new non-dominant solutions.
        """
        global pareto_front        
        current_swarm = list(self.get_pareto_objectives(swarm))
        indices_to_delete = []
        
        for i in range(len(current_swarm)):                                                      #cycle through swarm and compare objectives
            for j in range(len(current_swarm)):
                
                if i==j:                                                                         #no need to compare solution with itself 
                    continue
                
                particle_to_remove = self.pareto_remover(current_swarm[i], current_swarm[j])     #determine which solution is dominant 
                
                if particle_to_remove == False:                                                  #if neither are dominant, leave both in front
                    continue                
                else:
                    indices_to_delete.append(current_swarm.index(particle_to_remove))            #store index of solution if it is dominant
                
        indices_to_delete = sorted(set(indices_to_delete), reverse=True)
        for i in indices_to_delete:                                                              #remove dominating solutions 
            del swarm[i]
        pareto_front = list(swarm)                                                               #update global pareto_front
        
        
    def dump_fronts(self, fronts, iteration):
        """
        Function dumps data of current front in file in output directory e.g. fronts.1 will contain the first front calculated.
        
        Args:
            fronts: pareto-front to be dumped
            iteration: current iteration number
        Returns:
            None
        """
        global store_location
        
        f = file("{0}/FRONTS/fronts.{1}".format(store_location, iteration), "w")             #open file
        f.write("fronts = ((\n")
        for i, data in enumerate(fronts):
            f.write("    ({0}, {1}),\n".format(data[0], tuple(data[1])))                     #insert each solution in front
        f.write("),)\n")
        f.close()                                                                            #close file
        
        pass


    def normalised_front(self, front):
        
        
        front_x = [i[0] for i in front]
        front_y = [i[1] for i in front]

        max_x = max(front_x)
        max_y = max(front_y)
    
        min_x = min(front_x)
        min_y = min(front_y)

        x_norm = [(i-min_x)/(max_x-min_x) for i in front_x]
        y_norm = [(i-min_y)/(max_y-min_y) for i in front_y]

        front_norm = zip(x_norm,y_norm)
        return front_norm
    
    
    def get_leader_roulette_wheel(self):
        """
        Function that produces a roulette wheel selection list for solutions in pareto-front
        
        Args:
            current_swarm: list of Particle instances.
            
        Returns;
            roulette_wheel: list of roulette wheel probabilities inversely proportional to number of particles near each particle in the pareto-front.
        """
        global pareto_front
        
        if len(pareto_front) < 2:
            return []
        pareto_obj = self.get_pareto_objectives(pareto_front)
        swarm_size = len(pareto_obj)
        normalised_front = self.normalised_front(pareto_obj)
        kd_tree = spatial.KDTree(normalised_front)
        
        density = [len(kd_tree.query_ball_point(x=i, r=0.05))-1 for i in normalised_front]
        density_sum = sum(density)
        
        if density_sum == 0:
            inv_density = [1 for i in range(swarm_size)] 
        else :
            inv_density = [density_sum-i for i in density]
        
        inv_density_size = sum(inv_density)
        
        roulette_wheel = [inv_density[0]/inv_density_size]
        for i in range(1,swarm_size):
            cumulative_prob = roulette_wheel[i-1] + inv_density[i]/inv_density_size
            roulette_wheel.append(cumulative_prob)
        #print 'roulette wheel', roulette_wheel
        return roulette_wheel
       
       
    def evaluate(self, swarm, initial_evaluation=False):
        """
        Function evaluates objectives for the swarm and updates best positions for each particle instance
        
        Args:
            swarm: list of Particle instances
            initial_evaluation: this should be True if this is the first iteration.
        
        Returns:
            None, but updates all particle best locations in objective space for next iteration.
        """
        
        objectives = self.evaluate_swarm(swarm)                                    #obtain objective measurements and errors for all particles.
        for i in range(len(swarm)):                
            swarm[i].fit_i = objectives[i]                                                 #update current objective fit.
        
            if initial_evaluation==False:
                if self.pareto_test(swarm[i].fit_i,swarm[i].fit_best_i) == True:           #check if this objective fit is a personal best for the particle.
                    swarm[i].pos_best_i = swarm[i].position_i
                    swarm[i].fit_best_i = swarm[i].fit_i
                    
            if initial_evaluation==True:                                                   #for the first iteration, the fit will be the personal best. 
                swarm[i].fit_best_i = swarm[i].fit_i
                swarm[i].pos_best_i = swarm[i].position_i
                
    def optimise(self):
        """
        This function runs the optimisation algorithm. It initialises the swarm and then takes successive measurements whilst
        updating the location of the swarm. It also updates the pareto-front archive after each iteration.
        
        Args:
            None
            
        Returns:
            None, but the pareto-front archive will have been updated with the non-dominating front.        
        """
        
        global pareto_front
        global completed_iteration 
    
        swarm = []
        for i in range(0, self.swarm_size):                                                       #initialise the swarm 
            swarm.append(Particle(self.parameter_count, self.par_min, self.par_max))
        
        self.evaluate(swarm, initial_evaluation=True)   
        proposed_pareto = [[j.position_i,j.fit_i] for j in swarm]                         #define the front for sorting 
        self.find_pareto_front(proposed_pareto)                                                   #find the non-dominating set
        #front_to_dump = tuple(list(pareto_front))                                                 
        #self.dump_fronts(front_to_dump, 0)                                                        #dump new front in file
        completed_iteration = 1
         
        for t in range(1,self.maxiter):  
            print 'iteration', completed_iteration                                                        #begin iteration 
            leader_roullete_wheel = self.get_leader_roulette_wheel()                         #calculate leader roulette wheel for the swarm
            
            for j in range(0, self.swarm_size):                                                   #for every particle:                                               
                swarm[j].select_leader(leader_roullete_wheel)                                     #select leader
                swarm[j].update_velocity(self.inertia, self.social_parameter, self.cognitive_parameter)   #update velocity   
                swarm[j].update_position()                                                        #update position
             
            self.evaluate(swarm)                                                                  #evaluate new positions            
            proposed_pareto = [[j.position_i,j.fit_i] for j in swarm] + pareto_front      #define front for sorting
            self.find_pareto_front(proposed_pareto)                                               #find the non-dominating set
            #front_to_dump = list(pareto_front)                                                    #dump new front in file
            #self.dump_fronts(front_to_dump, t)
            
            completed_iteration += 1                                                               #track iteration number
            
        print "OPTIMISATION COMPLETE"
        front_to_dump = list(pareto_front)
        self.dump_fronts(front_to_dump, 0)
        return pareto_front
        
        

class Particle:
    
    def __init__(self, num_parameter, par_min, par_max):
        
        self.position_i = tuple([random.uniform(par_min[i],par_max[i]) for i in range(num_parameter)])        #particle's position
        self.velocity_i = tuple([random.uniform(par_min[i],par_max[i]) for i in range(num_parameter)])        #particle's velocity
        self.pos_best_i = ()                                                                                  #particle's best position
        self.leader_i = ()                                                                                    #particle's leader
        self.fit_i = ()                                                                                       #particle's fit 
        self.fit_best_i = ()                                                                                  #particle's best fit
        self.bounds = (par_min, par_max)                                                                      #particle's parameter bounds                                                                                         #particle's error in fit
             
             
    def update_velocity(self, inertia, social_param, cog_param):
        """
        Function updates particle velocity according to particle swarm velocity equation.
        
        Args:
            inertia: inertia parameter gives particles mass (float type).
            social_param: social parameter give particles an attraction to swarm's best locations (float type).
            cog_param: cognitive parameter gives a particle an attraction to its own best location.
        
        Returns:
            None, but updates the particle's velocity attribute.
        """
        new_velocity = list(self.velocity_i)
        
        for i in range(0, len(self.bounds[0])):                                                        #new velocity in each parameter dimension 
            
            r1 = random.random()                                                                       #random numbers between [-1,1] for random-walk nature of code
            r2 = random.random()
            
            velocity_cognitive = cog_param * r1 * (self.pos_best_i[i] - self.position_i[i])            #calculate cognitive velocity term
            velocity_social = social_param * r2 * (self.leader_i[i] - self.position_i[i])              #calculate social velocity term
            
            new_velocity[i] = inertia*new_velocity[i] + velocity_cognitive + velocity_social           #calculate new velocity
            
        self.velocity_i = tuple(new_velocity)                                                          #update particle  velocity attribute
    

    def update_position(self):
        """
        Function updates particle position according to particle swarm position equation.
        
        Args:
            None
        
        Returns:
            None, but updates the particle's position.
        """
        new_position = list(self.position_i)
        new_velocity = list(self.velocity_i)
        for i in range(0,len(self.bounds[0])):                                                         #new position in each parameter dimension
            new_position[i]= new_position[i] + self.velocity_i[i]                                      #calculate new position                                     
            
            if new_position[i] > self.bounds[1][i]:                                                    #reflect if particle goes beyond upper bounds
                new_position[i] = self.bounds[1][i]
                new_velocity[i] = -1 * new_velocity[i]
                
            if new_position[i] < self.bounds[0][i]:                                                    #reflect if particle goes below lower bounds
                new_position[i] = self.bounds[0][i]
                new_velocity[i] = -1 * new_velocity[i]
                
        self.velocity_i = tuple(new_velocity)                                                          #update particle velocity attribute                             
        self.position_i = tuple(new_position)                                                          #update particle position attribu   
            

    def select_leader(self, roulette_wheel):
        global pareto_front
        if len(pareto_front) < len(pareto_front[0][1]) +1:
            self.leader_i = random.choice(pareto_front)[0]                          
            return
        
        r = random.random()
        for i in range(len(pareto_front)):
            if r <= roulette_wheel[i]:
                self.leader_i = pareto_front[i][0]
                #print 'leader', Test_Functions.T1(self.leader_i)
            else:
                self.leader_i = random.choice(pareto_front)[0]
                #print 'leader', Test_Functions.T1(self.leader_i)