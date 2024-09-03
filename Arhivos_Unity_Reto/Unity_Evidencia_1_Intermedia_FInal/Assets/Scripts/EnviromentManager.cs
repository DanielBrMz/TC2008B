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
    [SerializeField] private float maxIterationDurationDepreciated = 1f; // Maximum duration for an iteration
    [SerializeField] private string apiUrl = "http://127.0.0.1:5000/gmes";
    public static float suggestedIterationDuration;
    [SerializeField] private int startupDelay = 5;
    [SerializeField] private int iterationDelay = 500;

    private List<Stack> allStacks = new List<Stack>();
    private int fullStackCount = 0;

    private List<PositionData> allAgentData = new List<PositionData>();


    private CancellationTokenSource _cts;
    private Task _simulationTask;

    private void Awake()
    {
        suggestedIterationDuration = maxIterationDurationDepreciated;
    }

    private void Start()
    {
        allStacks = new List<Stack>(FindObjectsOfType<Stack>());
        Stack.OnStackFull += HandleStackFull;
    }

    public async void Initialize()
    {
        await InitializeAgentPositions();
        await Task.Delay(startupDelay * 1000);
        await StartSimulation();
    }

    public async Task InitializeAgentPositions()
    {
        allAgentData.Clear(); // Clear the list before populating
        foreach (Agent agent in Enviroment.agents)
        {
            var sensorData = await agent.GetSensorData();

            PositionData data = new PositionData
            {
                id = agent.id,
                position = sensorData,
                // is_holding = agent.hasObject
            };
            allAgentData.Add(data);
        }
        Debug.Log($"Initialized {allAgentData.Count} agents;");
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
            await Task.Delay(iterationDelay, ct);
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

        // Ensure all sensor data is up to date
        await Task.Yield();

        allAgentData.Clear();
        // If it was successfull get the sensor data and do it again
        foreach (Agent agent in Enviroment.agents)
        {
            Dictionary<char, int> sensorData = new Dictionary<char, int>();
            foreach (char direction in new[] { 'F', 'B', 'L', 'R' })
            {
                sensorData[direction] = agent.sensors[direction].GetSensorValue();
            }

            PositionData data = new PositionData
            {
                id = agent.id,
                position = sensorData,
                // is_holding = agent.hasObject
            };
            allAgentData.Add(data);
        }

        Debug.Log($"Got info from {allAgentData.Count} agents;");
    }

    private async Task ExecuteAgentAction(ActionSintax action, CancellationToken ct)
    {
        if (ct.IsCancellationRequested) return;

        await Enviroment.agents[action.id].ExecuteAction(action);
    }

    private async Task<List<ActionSintax>> GetActionsFromServer(List<PositionData> data)
    {
        Debug.LogWarning("Request sent!!! ===>");
        string json = JsonConvert.SerializeObject(data);
        Debug.Log("Sent: " + json);
        string response = await Utils.SendGetRequestWithStructDataAsync(apiUrl, json);
        Debug.LogWarning("Resp: " + response);
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

    private void OnApplicationQuit()
    {
        StopSimulation();
    }

    private void HandleStackFull(Stack stack)
    {
        fullStackCount++;
        if (fullStackCount == allStacks.Count)
        {
            Debug.Log("Simulation success. All stacks are full");
            StopSimulation();
        }
    }

}

