using System.Collections;
using System.Collections.Generic;
using System.Data.Common;
using System.Threading.Tasks;
using UnityEditor;
using Newtonsoft.Json;
using UnityEngine;

public class EnvironmentManager : MonoBehaviour
{
    // Set this with a slider to set the delay in which in iteration is finished and we send the current enviroment info to the server
    [Header("Manager parameters")]
    [SerializeField] private float maxIterationDuration = 1f; // Maximum duration for an iteration
    public static float iterationDuration;

    private Dictionary<int, Dictionary<char, int>> agentSensorData = new Dictionary<int, Dictionary<char, int>>();
    private List<PositionData> allAgentData = new List<PositionData>();

    public delegate void AgentActionDelegate(int Id, ActionSintax action);
    public static event AgentActionDelegate OnAgentAction;

    private bool isSimulationRunning = false;

    // Instruction utility variables
    private int _i = 0;

    private void Awake()
    {
        iterationDuration = maxIterationDuration;
    }

    public async void Initialize()
    {
        InitializeAgentPositions();
        await StartSimulation();
    }

    public async void InitializeAgentPositions()
    {
        foreach (Agent agent in Enviroment.agents)
        {
            agentSensorData[agent.id] = await agent.GetSensorData();
            foreach (KeyValuePair<int, Dictionary<char, int>> kv in agentSensorData)
            {
                PositionData data = new PositionData
                {
                    id = kv.Key,
                    position = kv.Value
                };
                allAgentData.Add(data);
            }
        }
    }

    public async Task StartSimulation()
    {
        isSimulationRunning = true;

        while (isSimulationRunning)
        {
            // // Here you would send the collected data to the server and wait for new instructions
            // // For now, we'll just pause briefly
            await RunIteration();

            await Task.Delay(1000);
        }
    }

    private async Task RunIteration()
    {
        List<Task> agentTasks = new List<Task>();

        // Start all agent actions
        foreach (PositionData agent in allAgentData)
        {
            ActionSintax action = await GetActionFromServer(agent.id, agent);
            agentTasks.Add(ExecuteAgentAction(Enviroment.agents[agent.id - 1], action));
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
        foreach (KeyValuePair<int, Dictionary<char, int>> kv in agentSensorData)
        {
            PositionData smt = new PositionData
            {
                id = kv.Key,
                position = kv.Value
            };
            allAgentData.Add(smt);
        }
    }

    private async Task ExecuteAgentAction(Agent agent, ActionSintax action)
    {
        OnAgentAction?.Invoke(agent.id, action);
        await agent.ExecuteAction(action);
    }

    List<string> actions = new List<string>{
        "GB",
        "MF",
        "DF",
        "GL",
        "MR",
        "DF",
        "GR",
        "ML",
        "DF",
    };

    private async Task<ActionSintax> GetActionFromServer(int agentId, PositionData data)
    {
        // This is where you'd implement the logic to get the action from the server
        // For now, we'll just return a random action

        // PositionData smt = new PositionData
        // {
        //     id = 1,
        //     position = new Dictionary<char, int>
        //         {
        //             { 'F', 0 },
        //             { 'B', 0 },
        //             { 'L', 1 },
        //             { 'R', 1 }
        //         }
        // };

        string response = await Utils.SendGetRequestWithStructDataAsync(JsonConvert.SerializeObject(data));
        // Debug.Log(response);

        ActionSintax action = JsonConvert.DeserializeObject<ActionSintax>(response);
        // char randomDirection = Utils.Direction2Name(Utils.directions[Random.Range(0, Utils.directions.Length)]);
        // return GetNextAction(actions);
        return action;
    }

    private string GetNextAction(List<string> actions)
    {
        if (actions == null || actions.Count == 0)
        {
            StopSimulation();
        }

        if (_i >= actions.Count)
        {
            _i = 0; // Reset to the beginning if we've reached the end
        }

        return actions[_i++];
    }

    public void StopSimulation()
    {
        isSimulationRunning = false;
    }
}

