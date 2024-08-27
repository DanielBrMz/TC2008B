using System.Collections;
using System.Collections.Generic;
using System.Threading.Tasks;
using UnityEngine;

public class EnvironmentManager : MonoBehaviour
{
    // Set this with a slider to set the delay in which in iteration is finished and we send the current enviroment info to the server
    [Header("Manager parameters")]
    [SerializeField] private float maxIterationDuration = 1f; // Maximum duration for an iteration
    public static float iterationDuration;

    private Dictionary<int, Dictionary<char, int>> agentSensorData = new Dictionary<int, Dictionary<char, int>>();

    public delegate void AgentActionDelegate(int Id, string action);
    public static event AgentActionDelegate OnAgentAction;
    
    private bool isSimulationRunning = false;

    private void Awake()
    {
        iterationDuration = maxIterationDuration;
    }

    public async void Initialize()
    {
        await StartSimulation();
    }

    public async Task StartSimulation()
    {
        isSimulationRunning = true;
        while (isSimulationRunning)
        {
            await RunIteration();
            // Here you would send the collected data to the server and wait for new instructions
            // For now, we'll just pause briefly
            await Task.Delay(100);
        }
    }

    private async Task RunIteration()
    {
        List<Task> agentTasks = new List<Task>();

        // Start all agent actions
        foreach (Agent agent in Enviroment.agents)
        {
            string action = await GetActionFromServer(agent.id);
            agentTasks.Add(ExecuteAgentAction(agent, action));
        }

        // Wait for all actions to complete or for the max duration to elapse
        await Task.WhenAny(
            Task.WhenAll(agentTasks),
            Task.Delay((int)(maxIterationDuration * 1000))
        );

        // Collect sensor data from all agents
        foreach (Agent agent in Enviroment.agents)
        {
            agentSensorData[agent.id] = await agent.GetSensorData();
        }

        // Here you would process the agentSensorData and prepare it for sending to the server
    }

    private async Task ExecuteAgentAction(Agent agent, string action)
    {
        OnAgentAction?.Invoke(agent.id, action);
        await agent.ExecuteAction(action);
    }
    
    private async Task<string> GetActionFromServer(int agentId)
    {
        // This is where you'd implement the logic to get the action from the server
        // For now, we'll just return a random action
        await Task.Delay(20); // Simulating network delay
        char randomDirection = Utils.Direction2Name(Utils.directions[Random.Range(0, Utils.directions.Length)]);
        return $"M{randomDirection}";
        // return $"GF";
    }

    

    public void StopSimulation()
    {
        isSimulationRunning = false;
    }
}

