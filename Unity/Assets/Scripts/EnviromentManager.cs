using System.Collections;
using System.Collections.Generic;
using System.Data.Common;
using System.Threading.Tasks;
using UnityEditor;
using Newtonsoft.Json;
using UnityEngine;
using System.Threading;
using System;

public class EnvironmentManager : MonoBehaviour
{
    // Set this with a slider to set the delay in which in iteration is finished and we send the current enviroment info to the server
    [Header("Manager parameters")]
    [SerializeField] private float maxIterationDuration = 1f; // Maximum duration for an iteration
    [SerializeField] private string apiUrl = "http://127.0.0.1:5000/gmes";
    public static float iterationDuration;

    private Dictionary<int, Dictionary<char, int>> agentSensorData = new Dictionary<int, Dictionary<char, int>>();
    private List<PositionData> allAgentData = new List<PositionData>();


    private CancellationTokenSource _cts;
    private Task _simulationTask;

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
        _cts = new CancellationTokenSource();
        _simulationTask = RunSimulationLoop(_cts.Token);

        try
        {
            await _simulationTask;
        }
        catch (OperationCanceledException)
        {
            Debug.Log("Simulation was cancelled.");
        }
        catch (Exception ex)
        {
            Debug.LogError($"Simulation encountered an error: {ex}");
        }
    }

    private async Task RunSimulationLoop(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            await RunIteration(ct);
            await Task.Delay(1000, ct);
        }
    }

    private async Task RunIteration(CancellationToken ct)
    {
        List<Task> agentTasks = new List<Task>();
        // Send agentInfo to server and return list of actions
        List<ActionSintax> actions = await GetActionsFromServer(allAgentData);

        // Add all actions to agentTasks so they can be awaited
        foreach (var action in actions)
        {
            agentTasks.Add(ExecuteAgentAction(action, ct));
        }

        // Wait for all actions to complete or for the max duration to elapse
        await Task.WhenAny(
            Task.WhenAll(agentTasks)
            // Task.Delay((int)(maxIterationDuration * 1000))
        );

        // If the process is cancelled kill all threads
        if (ct.IsCancellationRequested) return;
        allAgentData.Clear();

        // If it was successfull get the sensor data and do it again
        foreach (Agent agent in Enviroment.agents)
        {
            agentSensorData[agent.id] = await agent.GetSensorData();
            PositionData smt = new PositionData
            {
                id = agent.id,
                position = agentSensorData[agent.id]
            };
            allAgentData.Add(smt);
        }
    }

    private async Task ExecuteAgentAction(ActionSintax action, CancellationToken ct)
    {
        if (ct.IsCancellationRequested) return;

        Debug.Log($"Ag{action.id} processing action");
        await Enviroment.agents[action.id].ExecuteAction(action);
    }

    private async Task<List<ActionSintax>> GetActionsFromServer(List<PositionData> data)
    {
        string response = await Utils.SendGetRequestWithStructDataAsync(apiUrl, JsonConvert.SerializeObject(data));
        return JsonConvert.DeserializeObject<List<ActionSintax>>(response);
    }

    public void StopSimulation()
    {
        _cts?.Cancel();
    }

    private void OnDestroy()
    {
        StopSimulation();
    }

    private void OnApplicationQuit() {
        StopSimulation();
    }
}

