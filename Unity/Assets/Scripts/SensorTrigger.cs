using UnityEngine;
// Trigger behaviour for the sensors
public class SensorTrigger : MonoBehaviour
{
  public Agent parentAgent;
  public char direction;
  private TextMesh numberDisplay;

  public int value = 0;

  private object _lock = new object();

  public void SetTextMesh(TextMesh textMesh)
  {
    numberDisplay = textMesh;
    UpdateDisplay();
  }

  public void UpdataDisplayValue()
  {
    UpdateDisplay();
  }

  private void UpdateDisplay()
  {
    if (numberDisplay != null)
    {
      numberDisplay.text = value.ToString();
    }
  }

  private void OnTriggerEnter(Collider other)
  {
    UpdateSensorValue(other);
  }

  private void OnTriggerStay(Collider other)
  {
    UpdateSensorValue(other);
  }

  private void OnTriggerExit(Collider other)
  {
    lock (_lock)
    {
      value = 0;
      parentAgent.UpdateSensorValue(direction, 0);
      UpdateDisplay();
    }
  }

  private void UpdateSensorValue(Collider other)
  {
    lock (_lock)
    {
      int newValue = Utils.DetermineColliderType(other.gameObject.layer);
      if (newValue != value)
      {
        value = newValue;
        parentAgent.UpdateSensorValue(direction, value);
        UpdateDisplay();
      }
    }
  }

  public void ClearSensorValue()
  {
    lock (_lock)
    {
      value = 0;
      parentAgent.UpdateSensorValue(direction, 0);
      UpdateDisplay();
    }
  }

  public void ForceUpdate()
  {
    Collider[] colliders = Physics.OverlapSphere(transform.position, GetComponent<SphereCollider>().radius, LayerMask.GetMask("Objects", "Obstacles", "Stacks"));

    if (colliders.Length > 0)
    {
      int newValue = Utils.DetermineColliderType(colliders[0].gameObject.layer);
      value = newValue;
    }
    else
    {
      SetSensorValue(0);
    }

    UpdateDisplay();
  }

  private void LateUpdate()
  {

    UpdataDisplayValue();
  }

  public void SetSensorValue(int n)
  {
    value = n;
  }

  public int GetSensorValue()
  {
    return value;
  }
}